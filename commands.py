import datetime
import os
import sys
from datetime import datetime as dt
from hardware_state import action
from rule_state import rule

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

################################### alarm commands #################################

help_strings["alarm"] = "alarm <sub command> : commands for setting and modifying alarms"
def cmd_alarm(state, params):
    subcommands = {"add" : cmd_alarm_add,
                   "list" : cmd_alarm_list,
                   "delete" : cmd_alarm_delete}

    if params:
        if params[0] in subcommands:
            return subcommands[params[0]](state, params[1:])

    return cmd_help(state, ["alarm"])


help_strings["alarm"] += "\n\t- add <hour>:<minute> [sensor] [mode] : sets an alarm\n\t\tmode can be: \"daily\", \"single\""
def cmd_alarm_add(state, params):
    if len(params) >= 1:
        time = dt.now()
        sensor = "alarm"
        mode = "daily"

        try:
            time = dt.combine(time.date(), dt.strptime(params[0], "%H:%M").time())
        except:
            return "invalid time format\n"

        if len(params) > 1:
            sensor = params[1]

        if len(params) > 2:
            if params[2] in ["daily", "single"]:
                mode = params[2]
            else:
                return "invalid repetition type"

        state.alarm_state.add_alarm(time, sensor, mode)
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

############################## sensor commands ###################################

help_strings["sensor"] = "sensor : commands to manage sensors:"
def cmd_sensor(state, params):
    subcommands = {"add" : cmd_sensor_add,
                   "known": cmd_sensor_known,
                   "list": cmd_sensor_list}

    if params:
        if params[0] in subcommands:
            return subcommands.get(params[0])(state, params[1:])

    return cmd_help(state, ["sensor"])

help_strings["sensor"] += "\n\t- add <id> : adds the sensor with the specified ID"
def cmd_sensor_add(state, params):
    if not params:
        return "id field missing\n"
    if params[0] in state.hardware_state.actions:
        return "already defined as an action\n"

    state.hardware_state.add_sensor(params[0])
    return "sensor added\n"

help_strings["sensor"] += "\n\t- known : lists all sensors that were encountered by their input, registered or not"
def cmd_sensor_known(state, params):
    list_str = ""
    for name in state.hardware_state.encountered_sensors:
        list_str += name + "\n"
    return list_str

help_strings["sensor"] += "\n\t- list : lists all registered sensors"
def cmd_sensor_list(state, params):
    list_str = ""
    for s in state.hardware_state.sensors:
        list_str += s + "\n"

    return list_str

############################ FIFO commands ########################################

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

############################### action commands #####################################

help_strings["action"] = "action : commands for managing actions"
def cmd_action(state, params):
        subcommands = {"add" : cmd_action_add,
                       "list" : cmd_action_list,
                       "delete" : cmd_action_delete}

        if params:
            if params[0] in subcommands:
                return subcommands[params[0]](state, params[1:])

        return cmd_help(state, ["action"])

help_strings["action"] += "\n\t- add <id> <fifo> <value> : adds an action"
help_strings["action"] += "\n\t\t- id : the name of the action to refer to later"
help_strings["action"] += "\n\t\t- target : a registered fifo or sensor to write the action to"
help_strings["action"] += "\n\t\t         ->  note that in case of a sensor target the value must be numeric"
help_strings["action"] += "\n\t\t- value : value to be written to the fifo"
def cmd_action_add(state, params):
    if len(params) < 3:
        return "usage: action add <id> <target> <value>\n"
    if params[0] in state.hardware_state.sensors:
        return "already defined as a sensor\n"
    act = action()
    act.id = params[0]
    act.target = params[1]
    act.value = params[2]
    # the value parameter is greedy
    for p in params[3:]:
        act.value += " " + p
    state.hardware_state.add_action(act)
    return "action added\n"

help_strings["action"] += "\n\t- list : lists all registered actions"
def cmd_action_list(state, params):
    list_str = ""
    for act in state.hardware_state.actions.values():
        list_str += act.id + \
        "\ttarget=" + str(act.target) + \
        "\tvalue=\"" + str(act.value) + "\"\n"


    return list_str

help_strings["action"] += "\n\t- delete <id> : deletes the action with ID <id>"
def cmd_action_delete(state, params):
    if not params:
        return "usage: action delete <id>\n"
    if not state.hardware_state.delete_action(params[0]):
        return "no such action"
    return "action deleted"

############################## chain commands ##################################

help_strings["chain"] = "chain <sub command> : commands for managing chains"
def cmd_chain(state, params):
    subcommands = {"add" : cmd_chain_add,
                   "list" : cmd_chain_list,
                   "delete" : cmd_chain_delete}

    if params:
        if params[0] in subcommands:
            return subcommands[params[0]](state, params[1:])

    return cmd_help(state, ["chain"])

help_strings["chain"] += "\n\t- add <id> : adds a new chain with ID <id>"
def cmd_chain_add(state, params):
    if not params:
        return "id parameter missing\n"
    state.rule_state.add_chain(params[0])
    return "chain added\n"

help_strings["chain"] += "\n\t- list [id] : lists either chain [id] or all chains including their rules"
def cmd_chain_list(state, params):
    if params:
        if params[0] in state.rule_state.chains:
            return state.rule_state.chains[params[0]].dump_str()
        return "no such chain\n"

    list_str = ""
    for chn in state.rule_state.chains.values():
        list_str += chn.dump_str() + "\n"
    return list_str

help_strings["chain"] += "\n\t- delete <id> : deletes the chain with ID <id> including its rules"
def cmd_chain_delete(state, params):
    if not params:
        return "id parameter missing\n"
    state.rule_state.delete_chain(params[0])
    return "chain deleted\n"

############################## rule commands ###################################

help_strings["rule"] = "rule <sub command> : commands for managing rules within chains"
def cmd_rule(state, params):
        subcommands = {"add" : cmd_rule_add,
                       "insert" : cmd_rule_insert,
                       "delete": cmd_rule_delete}

        if params:
            if params[0] in subcommands:
                return subcommands[params[0]](state, params[1:])

        return cmd_help(state, ["rule"])

help_strings["rule"] += "\n\t- add <chain> <sensor> <min> <max> [action] [timeout]"
help_strings["rule"] += "\n\t\t- adds a rule to the end of <chain>"
def cmd_rule_add(state, params, index=sys.maxsize):
    if len(params) < 4:
        return "usage: rule add <chain> <sensor> <min> <max> [action] [timeout]\n"
    if params[0] not in state.rule_state.chains:
        return "no such chain\n"
    rl = rule()

    rl.sensor = params[1]
    rl.min_value = int(params[2])
    rl.max_value = int(params[3])
    if len(params) > 4 and params[4] != "-":
        rl.action = params[4]
    if len(params) > 5:
        rl.timeout = int(params[5])
    state.rule_state.add_rule(params[0], rl, index)    # append rule to the end
    return "rule added\n"

help_strings["rule"] += "\n\t- insert <index> <chain> <sensor> <min> <max> [action] [timeout]"
help_strings["rule"] += "\n\t\t- adds a rule to chain right before the rule with <index>"
def cmd_rule_insert(state, params):
    if len(params) < 5:
        return "usage: <index> <chain> <sensor> <min> <max> [action] [timeout]\n"
    return cmd_rule_add(state, params[1:], int(params[0]))

help_strings["rule"] += "\n\t- delete <chain> <index> : removes the rule at <index> from <chain>"
def cmd_rule_delete(state, params):
    if len(params) < 2:
        return "usage: rule delete <chain> <index>\n"
    if params[0] not in state.rule_state.chains:
        return "no such chain\n"
    chn = state.rule_state.chains[params[0]]
    if not chn.delete_rule(int(params[1])):
        return "rule index out of range\n"
    return "rule deleted\n"
