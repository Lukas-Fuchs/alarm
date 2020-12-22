import datetime
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

help_strings["alarm"] = "alarm <hour>:<minute> [mode] : sets an alarm\n\tmode can be: \"daily\", \"single\""
def cmd_alarm(state, params):
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

help_strings["list"] = "list : shows all alarms"
def cmd_list(state, params):
    list_str = ""
    for i in range(len(state.alarm_state.alarms)):
        alarm = state.alarm_state.alarms[i]
        list_str += str(i) + " | " + alarm.time.strftime("%H:%M") + " (" + alarm.mode + ")\n"
    return list_str

help_strings["delete"] = "delete <id>: deletes the alarm with the id given"
def cmd_delete(state, params):
    if params:
        if int(params[0]) < len(state.alarm_state.alarms):
            state.alarm_state.delete_alarm(state.alarm_state.alarms(int(params[0])))
            return "alarm deleted\n"
        return "no such alarm\n"
    return cmd_help(state, ["delete"])

help_strings["sensor"] = "sensor : various commands to manage sensors:\n"
def cmd_sensor(state, params):
    subcommands = {"add" : cmd_sensor_add}

    if params:
        if params[0] in subcommands:
            return subcommands.get(params[0])(state, params[1:])

    return cmd_help(state, ["sensor"])

help_strings["sensor"] += " - add <id> : adds the sensor with the specified ID"
def cmd_sensor_add(state, params):
    if not params:
        return "id field missing\n"
    sens = sensor()
    sens.id = params[0]
    sens.trivial_name = sens.id
    state.hardware_state.add_sensor(sens)
    return "sensor added\n"
