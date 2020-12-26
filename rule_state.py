import threading
from threading import Lock
import datetime
from datetime import datetime as dt

class rule:
    sensor = ""

    # accepting value range for the sensor
    min_value = 0
    max_value = 0

    # time in seconds to wait for the rule to be accepted (-1 means wait forever)
    timeout = -1

    # action to trigger on acceptance
    action = ""

    # indicates whether this rule has been prepared for checking
    _ready = False

    _time_start = dt.now()

    def check(self, value):
        if not self._ready:
            self._time_start = dt.now()
        accept = self.min_value <= value <= self.max_value
        #print(str(value))
        advance = accept
        if self.timeout >= 0:
            advance = advance or (dt.now() - self._time_start).total_seconds() >= self.timeout
        self._ready = not advance       # unless the chain advances this rule's times will still be correct
        return accept, advance



class chain:
    id = ""
    rules = []

    _current_index = 0

    _lock = threading.Lock()

    def __init__(self):
        self.rules = []

    def add_rule(self, rl, index):
        with self._lock:
            if index >= len(self.rules):
                self.rules.append(rl)
                return
            self.rules.insert(rl, index)

    def delete_rule(self, index):
        with self._lock:
            if index >= len(self.rules):
                return False
            del self.rules[index]
            return True

    def poll(self, sensors):
        act = ""    # the action to be performed if any

        if self._current_index >= len(self.rules):
            if not self.rules:
                return act
            self._current_index = 0  # overrange indicates overflow

        rl = self.rules[self._current_index]
        #print("checking sensor " + rl.sensor + " " + str(rl.min_value) + " " + str(rl.max_value) + " in chain " + self.id)
        if rl.sensor not in sensors:
            return act
        #print(sensors)
        accept, advance = rl.check(sensors[rl.sensor])
        if accept:
            act = rl.action
        if advance:
            self._current_index += 1
            self._current_index %= len(self.rules)
        return act

    def dump_str(self):
        list_str = "CHAIN " + self.id + "\n"
        for index in range(len(self.rules)):
            rl = self.rules[index]
            list_str += " " + str(index) + " | sensor=" + rl.sensor \
             + "\tmin=" + str(rl.min_value) \
             + "\tmax="+ str(rl.max_value) \
             + "\taction=" + rl.action \
             + "  \ttimeout=" + str(rl.timeout) \
             +  "\n"
        return list_str


class rule_state:
    chains = {}

    lock = threading.Lock()
    block_saving = False

    def __init__(self):
        self.chains = {}

    def add_chain(self, id):
        with self.lock:
            chn = chain()
            chn.id = id
            self.chains[id] = chn

    def add_rule(self, chain_id, rl, index):
        with self.lock:
            if chain_id in self.chains:
                self.chains[chain_id].add_rule(rl, index)
                self.save()

    def delete_chain(self, id):
        if id not in self.chains:
            return False
        with self.lock:
            del self.chains[id]
            return True

    def clear(self):
        with self.lock:
            self.chains = {}

    # Saves the hardware state as a sequence of commands that would recreate that state
    def save(self):
        if self.block_saving:
            return

        out = open("rule_state.dat", "w")
        for chn in self.chains.values():
            out.write("chain add " + chn.id + "\n")
            for rl in chn.rules:
                action_str = rl.action
                if not action_str:
                    action_str = "-"
                out.write("rule add " + chn.id + " " + rl.sensor + " " + str(rl.min_value) + " " + str(rl.max_value) + " " + action_str + " " + str(rl.timeout) + "\n")

        out.close()
