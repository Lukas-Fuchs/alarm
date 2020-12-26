from alarm_state import *
from hardware_state import *
from rule_state import *

class state:
    alarm_state = alarm_state()
    hardware_state = hardware_state()
    rule_state = rule_state()

    def clear(self):
        self.alarm_state.clear()
        self.hardware_state.clear()
        self.rule_state.clear()

    def block_saving(self, block):
        self.alarm_state.block_saving = block
        self.hardware_state.block_saving = block
        self.rule_state.block_saving = block
