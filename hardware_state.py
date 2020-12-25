import datetime
from datetime import datetime as dt
import threading
from threading import Lock
import os


class sensor:
    id = ""                 # identifier; name that the sensor identifies itself with
    trivial_name = ""       # intuitive name that may be set by the user
    type = ""               # type of sensor; may be relevant for interpreting signals

    # the default settings are for a stable sensor with refresh rate < 1s
    t_rising = 0            # time (in s) required to interpret signals as activation
    t_falling = 1           # time (in s) required to interpret no-signal as deactivation

    # setting both of these to the same number results in everything greater
    # to be interpreted as on
    threshold_rising = 0    # signal level required to interpret as on
    threshold_falling = 0   # max signal level to be interpreted as off

    ###### run time state ######

    # If this is true save() won't have any effect.
    # This can be helpful to prevent saving when replaying changes to the state
    block_saving = False

    _activated = False
    _signal_level = 0

    # a run is defined as a series of equal logic levels over a period of time
    _run_value = False
    _run_start = dt.now()

    # called whenever a signal is received from this sensor
    def signal(self, level):
        print("signal " + str(level) + " for sensor " + self.id)
        run_time = (dt.now() - self._run_start).total_seconds()
        would_activate = not level <= self.threshold_falling and level >= self.threshold_rising

        if would_activate != self._run_value:
            self._run_start = dt.now()
            run_time = 0
            self._run_value = would_activate

        if (would_activate and run_time >= self.t_rising) or (not would_activate and run_time >= self.t_falling):
            self._activated = would_activate

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


    def add_sensor(self, s):
        with self.lock:
            self.sensors[s.id] = s
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

    def add_action(self, act):
        self.actions[act.id] = act
        self.save()

    def delete_action(self, id):
        if id in self.actions:
            del self.actions[id]
            self.save()
            return True
        return False


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
