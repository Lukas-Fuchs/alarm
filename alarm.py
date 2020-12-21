import socket
import threading
import time
from commands import *
from alarm_state import *

state = alarm_state()

def telnet_command(line):
    words = line.split()
    if not words:
        return ""
    command = words[0]
    params = words[1:]

    commands = {
        "help" : cmd_help,
        "alarm" : cmd_alarm,
        "list" : cmd_list,
        "delete" : cmd_delete
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
            data = conn.recv(1024).decode("utf_8", "ignore")
            if not data:
                break

            conn.send(telnet_command(data).encode("utf_8", "ignore"))

        conn.close()


# periodically poll alarm state for alarms that are ready to be triggered
def alarm_polling_loop():
    while True:
        if state.poll():
            print("alarm triggered")
        time.sleep(20)

# load and replay commands that build the saved state
state.clear()
state.block_saving = True
save_file = open("alarm_state.dat", "r")
save_lines = save_file.readlines()
save_file.close()
for command in save_lines:
    telnet_command(command)
state.block_saving = False
state.save()

# start the server for handling telnet commands
server_thread = threading.Thread(target=server_main)
server_thread.start()

alarm_polling_loop()