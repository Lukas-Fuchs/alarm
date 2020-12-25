import datetime
from datetime import datetime as dt
import threading
from threading import Lock
import os


class sensor:
    id = ""                 # identifier; name that the sensor identifies itself with
    type = ""               # type of sensor; may be relevant for interpreting signals

    ###### run time state ######

    # If this is true save() won't have any effect.
    # This can be helpful to prevent saving when replaying changes to the state
    block_saving = False

    signal_level = 0

    # called whenever a signal is received from this sensor
    def signal(self, level):
        print("signal " + str(level) + " for sensor " + self.id)
        self.signal_level = level

# pretty simple data class to describe actions to be taken as rule consequences
class action:
    # unique identifier for this action; used to reference it further
    id = ""
    # fifo to write to
    fifo = ""
    # what to write to the fifo;
    # this will usually be something a process at the other end of the fifo can understand.
    value = ""


class hardware_state:
    # holds all sensors, the key being the sensor's id.
    sensors = {}
    # all sensor identifiers (registered or not) that have been encountered
    encountered_sensors = []

    # all fifos to get information from
    fifos = {}

    # all registered actions
    actions = {}

    lock = threading.Lock()


    def add_sensor(self, id):
        with self.lock:
            s = sensor()
            s.id = id
            self.sensors[id] = s
            if id not in encountered_sensors:
                encountered_sensors.append(id)
            self.save()

    def add_fifo(self, ff_name):
        with self.lock:
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
        with self.lock:
            if ff_name in self.fifos:
                self.fifos[ff_name].close()
                del self.fifos[ff_name]
                self.save()

    # This is intended for parallel-thread use.
    def write_fifo(self, ff_name, message):
        if ff_name in self.fifos:
            self.lock.acquire(blocking=False)
            self.fifos[ff_name].write(bytes(message + "\n", "utf-8"))
            self.fifos[ff_name].flush()
            self.lock.release()

    def add_action(self, act):
        with self.lock:
            self.actions[act.id] = act
            self.save()

    def delete_action(self, id):
        with self.lock:
            if id in self.actions:
                del self.actions[id]
                self.save()
                return True
            return False

    def perform_action(self, id):
        if id in self.actions:
            act = self.actions[id]
            writing_thread = threading.Thread(target=self.write_fifo, args=(act.fifo, act.value,))
            writing_thread.start()

    def clear(self):
        with self.lock:
            self.sensors = {}
            for key in self.fifos:
                self.fifos[key].close()
            self.fifos = {}

    # Saves the hardware state as a sequence of commands that would recreate that state
    def save(self):
        if self.block_saving:
            return

        out = open("hardware_state.dat", "w")
        for key in self.sensors:
            sens = self.sensors[key]
            out.write("sensor add " + sens.id + " " + str(sens.t_rising)
            + " " + str(sens.t_falling)
            + " " + str(sens.threshold_rising)
            + " " + str(sens.threshold_falling) + "\n")

        for ff_name in self.fifos:
            out.write("fifo add " + ff_name + "\n")

        for act in self.actions.values():
            out.write("action add " + act.id + " " + act.fifo + " " + act.value + "\n")

        out.close()
