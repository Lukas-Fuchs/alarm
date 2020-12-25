import socket
import threading
import time
from commands import *
from state import *
from hardware_listener import *

state = state()

def telnet_command(line):
    words = line.split()
    if not words:
        return ""
    command = words[0]
    params = words[1:]

    commands = {
        "help" : cmd_help,
        "alarm" : cmd_alarm,
        "sensor" : cmd_sensor,
        "fifo" : cmd_fifo,
        "action" : cmd_action,
        "ls" : cmd_ls
            }

    if command in commands:
        return commands.get(command)(state, params)
    return "command not found\n"


def server_main():
    host = ""
    port = 23

    srv_socket = socket.socket()
    srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv_socket.bind((host, port))
    srv_socket.listen(2)

    while True:
        print("waiting for connection...")
        conn, address = srv_socket.accept()
        print("connection from " + str(address))
        #_ = conn.recv(1024) # telnet sends junk on connection

        while True:
            conn.send(("> ").encode("utf_8", "ignore"))
            data = conn.recv(1024).decode("utf_8", "ignore")
            if not data:
                break

            conn.send(telnet_command(data).encode("utf_8", "ignore"))

        conn.close()


# periodically poll alarm state.alarm_state for alarms that are ready to be triggered
def alarm_polling_loop():
    while True:
        al = state.alarm_state.poll()
        if al:
            print("alarm triggered")
            state.hardware_state.perform_action(al.action)
        time.sleep(20)

# load and replay commands that build the saved state.alarm_state
def replay_file(fname):
    # first touch the file to make sure it exists
    save_file = open(fname, "a")
    save_file.close()

    save_file = open(fname, "r")
    save_lines = save_file.readlines()
    save_file.close()
    for command in save_lines:
        telnet_command(command)

state.clear()
state.block_saving(True)
replay_file("alarm_state.dat")
replay_file("hardware_state.dat")
state.block_saving(False)

# start the server for handling telnet commands
server_thread = threading.Thread(target=server_main)
server_thread.start()

fifo_thread = threading.Thread(target=fifo_listener, args=(state.hardware_state,))
fifo_thread.start()

alarm_polling_loop()
