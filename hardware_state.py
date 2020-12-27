import datetime
from datetime import datetime as dt
import threading
from threading import Lock
import os

# pretty simple data class to describe actions to be taken as rule consequences
class action:
    # unique identifier for this action; used to reference it further
    id = ""
    # fifo to write to
    target = ""
    # what to write to the fifo;
    # this will usually be something a process at the other end of the fifo can understand.
    value = ""


class hardware_state:
    # holds all sensor states, the key being the sensor's id
    # and the value the last signal encountered.
    sensors = {}
    # all sensor identifiers (registered or not) that have been encountered
    encountered_sensors = []

    # all fifos to get information from
    fifos = {}

    # all registered actions
    actions = {}

    # locks that block reading and writing respectively
    lock_read = threading.Lock()
    lock_write = threading.Lock()


    def add_sensor(self, id):
        with self.lock_read:
            self.sensors[id] = 0
            if id not in self.encountered_sensors:
                self.encountered_sensors.append(id)
            self.save()

    def add_fifo(self, ff_name):
        with self.lock_read:
            try:
                fifo_fd = os.open(ff_name, os.O_RDWR)
                os.set_blocking(fifo_fd, False)
                fifo = os.fdopen(fifo_fd, "rb+", 0)

                if fifo:
                    self.fifos[ff_name] = fifo
                    self.save()
                    return True
            except IOError as e:
                print(e)
                return False
            return False

    def delete_fifo(self, ff_name):
        with self.lock_read, self.lock_write:
            if ff_name in self.fifos:
                self.fifos[ff_name].close()
                del self.fifos[ff_name]
                self.save()

    # This is intended for parallel-thread use.
    def write_fifo(self, ff_name, message):
        if ff_name in self.fifos:
            with self.lock_write:
                self.fifos[ff_name].write(bytes(message + "\n", "utf-8"))
                self.fifos[ff_name].flush()

    def add_action(self, act):
        self.actions[act.id] = act
        self.save()

    def delete_action(self, id):
        if id in self.actions:
            with self.lock_read, self.lock_write:
                del self.actions[id]
                self.save()
                return True
        return False

    def perform_action(self, id):
        if id in self.actions:
            act = self.actions[id]
            try:
                if act.target in self.fifos:
                    writing_thread = threading.Thread(target=self.write_fifo, args=(act.target, act.value,))
                    writing_thread.start()
                elif act.target in self.sensors:
                    int_value = int(act.value)
                    self.sensors[act.target] = int_value
            except:
                # there are a number of things that can go wrong here, none of which matter really
                pass
            return

    def clear(self):
        with self.lock_read, self.lock_write:
            self.sensors = {}
            for key in self.fifos:
                self.fifos[key].close()
            self.fifos = {}

    # Saves the hardware state as a sequence of commands that would recreate that state
    def save(self):
        if self.block_saving:
            return

        out = open("hardware_state.dat", "w")
        for id in self.sensors:
            out.write("sensor add " + id + "\n")

        for ff_name in self.fifos:
            out.write("fifo add " + ff_name + "\n")

        for act in self.actions.values():
            out.write("action add " + act.id + " " + act.target + " " + act.value + "\n")

        out.close()
