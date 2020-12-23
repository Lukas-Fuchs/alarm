import datetime
import os
from datetime import datetime as dt
from hardware_state import sensor

help_strings = {}

help_strings["help"] = "help [command] : displays help for [command] or for all commands if none is specified."
def cmd_help(state, params):
    if len(params) > 0:
        if params[0] in help_strings:
            return help_strings.get(params[0]) + "\n"
        else:
            return "no help found for this command\n"
    else:
        full_help = ""
        for val in help_strings.values():
            full_help += val + "\n"
        return full_help

help_strings["alarm"] = "alarm <sub command> : commands for setting and modifying alarms"
def cmd_alarm(state, params):
    subcommands = {"add" : cmd_alarm_add,
                   "list" : cmd_alarm_list,
                   "delete" : cmd_alarm_delete}

    if params:
        if params[0] in subcommands:
            return subcommands[params[0]](state, params[1:])

    return cmd_help(state, ["alarm"])


help_strings["alarm"] += "\n\t- add <hour>:<minute> [mode] : sets an alarm\n\t\tmode can be: \"daily\", \"single\""
def cmd_alarm_add(state, params):
    if params:
        time = dt.now()
        mode = "daily"

        time = dt.combine(time.date(), dt.strptime(params[0], "%H:%M").time())

        if len(params) > 1:
            if params[1] in ["daily", "single"]:
                mode = params[1]
            else:
                return "invalid repetition type"

        state.alarm_state.add_alarm(time, mode)
        return "alarm set\n"
    return cmd_help(state, ["alarm"])

help_strings["alarm"] += "\n\t- list : shows all alarms"
def cmd_alarm_list(state, params):
    list_str = ""
    for i in range(len(state.alarm_state.alarms)):
        alarm = state.alarm_state.alarms[i]
        list_str += str(i) + " | " + alarm.time.strftime("%H:%M") + " (" + alarm.mode + ")\n"
    return list_str

help_strings["alarm"] += "\n\t- delete <id> : deletes the alarm with the id given"
def cmd_alarm_delete(state, params):
    if params:
        index = int(params[0])
        if 0 <= index < len(state.alarm_state.alarms):
            state.alarm_state.delete_alarm(state.alarm_state.alarms[index])
            return "alarm deleted\n"
        return "no such alarm\n"
    return cmd_help(state, ["alarm"])

help_strings["sensor"] = "sensor : commands to manage sensors:"
def cmd_sensor(state, params):
    subcommands = {"add" : cmd_sensor_add,
                   "known": cmd_sensor_known}

    if params:
        if params[0] in subcommands:
            return subcommands.get(params[0])(state, params[1:])

    return cmd_help(state, ["sensor"])

help_strings["sensor"] += "\n\t- add <id> : adds the sensor with the specified ID"
def cmd_sensor_add(state, params):
    if not params:
        return "id field missing\n"
    sens = sensor()
    sens.id = params[0]
    sens.trivial_name = sens.id
    state.hardware_state.add_sensor(sens)
    return "sensor added\n"

help_strings["sensor"] += "\n\t- known : lists all sensors that were encountered by their input, registered or not"
def cmd_sensor_known(state, params):
    list_str = ""
    for name in state.hardware_state.encountered_sensors:
        list_str += name + "\n"
    return list_str

help_strings["fifo"] = "fifo <sub command> : commands to manage FIFOs"
def cmd_fifo(state, params):
        subcommands = {"add" : cmd_fifo_add,
                       "list" : cmd_fifo_list,
                       "delete" : cmd_fifo_delete}

        if params:
            if params[0] in subcommands:
                return subcommands[params[0]](state, params[1:])

        return cmd_help(state, ["fifo"])

help_strings["fifo"] += "\n\t- add <file> : adds file <file> as a FIFO"
def cmd_fifo_add(state, params):
    if not params:
        return "FIFO file missing\n"
    if state.hardware_state.add_fifo(params[0]):
        return "FIFO added\n"
    return "failed to add FIFO\n"

help_strings["fifo"] += "\n\t- list : lists all active FIFOs"
def cmd_fifo_list(state, params):
    list_str = ""
    for ff_name in state.hardware_state.fifos.keys():
        list_str += ff_name + "\n"
    return list_str

help_strings["fifo"] += "\n\t - delete <fifo> : deletes (closes) FIFO <fifo>"
def cmd_fifo_delete(state, params):
        if params:
            if params[0] in state.hardware_state.fifos:
                state.hardware_state.delete_fifo(params[0])
                return "FIFO deleted\n"
            return "no such FIFO\n"
        return cmd_help(state, ["fifo"])

help_strings["ls"] = "ls : lists the working directory (useful for finding FIFOs)"
def cmd_ls(state, params):
    list_str = ""
    for root, dirs, files in os.walk("."):
        list_str += root + "\n"
        for fname in files:
            list_str += "\t" + fname + "\n"
    return list_str
