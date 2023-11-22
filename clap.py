import sys
import json
from typing import List


def IsKnown(arg: str, config: dict) -> bool:
    name = GetArgName(arg)
    type = GetArgType(arg)

    if "arguments" in config:
        if not name in config["arguments"]:
            return False
        else:
            return type == config["arguments"][name]["type"]
    else:
        return False


def IsValue(obj: dict):
    return "val" in obj


def IsSettingSet(setting: str, config: dict) -> bool:
    if "settings" in config:
        if setting in config["settings"]:
            return True
    return False


def GetSetting(setting: str, default: any, config: dict) -> any:
    if IsSettingSet(setting, config):
        return config["settings"][setting]
    else:
        return default


def GetVal(val: str) -> dict:
    if val.lstrip('-').isdigit():
        return {"type": "number", "val": val}

    return {"type": "string", "val": val}


def GetArgType(arg: str) -> str:
    dash_count = arg.count("-")

    if len(arg) <= 1:
        return "command"

    if arg[1] == "-" and dash_count <= 2:
        return "--"
    elif dash_count == 1:
        return "-"
    elif dash_count > 0:
        return "---"
    else:
        return "command"


def GetArgName(arg: str) -> str:
    return arg.replace("-", "")


def InferrParameters(arg: str, config: dict) -> dict:
    arg_name = GetArgName(arg)
    arg_type = GetArgType(arg)

    if arg_type == "command":
        return GetVal(arg)

    arg_count = GetSetting("default_count", 0, config)

    return {"name": arg_name, "type": arg_type, "count": arg_count, "known": False}


def FindParameters(arg: str, config: dict) -> dict:
    name = arg.replace("-", "")

    if not IsKnown(arg, config):
        return InferrParameters(arg, config)

    return {"name": name, "type": config["arguments"][name]["type"],
            "count": config["arguments"][name]["count"], "known": True}


def FindArgs(arg_index: int, arguments: List[str], config: dict) -> dict:
    if arg_index >= len(arguments):
        return {}

    parameters = FindParameters(arguments[arg_index], config)

    if IsValue(parameters):
        return parameters

    arg = {"name": GetArgName(arguments[arg_index]), "type": GetArgType(
        arguments[arg_index]), "known": parameters["known"], "args": []}

    count = 0

    for i in range(1, parameters["count"] + 1):
        if arg_index + i >= len(arguments):
            break

        if IsKnown(arguments[arg_index + i], config):
            arg["args"].append(FindArgs(arg_index + i, arguments, config))
            count += 1
        else:
            arg["args"].append(GetVal(arguments[arg_index + i]))
            count += 1

    for i in range(0, len(arg["args"])):
        if "count" in arg["args"][i]:
            count += arg["args"][i]["count"]

    arg["count"] = count

    return arg


def SplitSegments(segments: str) -> List[str]:
    arg_type = GetArgType(segments)

    if not arg_type == "---":
        return [segments]

    cur = segments.find("-", 0)

    ret = []

    while not cur == -1:
        next = segments.find("-", cur + 2)

        if next == -1:
            ret.append(segments[cur:len(segments)])
        else:
            ret.append(segments[cur:next])

        cur = next

    return ret


def ListArgumentsofType(type: str, config: dict) -> List[str]:
    if not "arguments" in config:
        return []

    ret = []
    for key in config["arguments"]:
        if config["arguments"][key]["type"] == type:
            ret.append(key)

    return ret


def MatchSingle(arg_seg_name: str, config: dict) -> List[str]:
    ret = []

    while IsKnown("-" + arg_seg_name[0], config):
        ret.append("-" + arg_seg_name[0])
        arg_seg_name = arg_seg_name[1:len(arg_seg_name)]
        if len(arg_seg_name) == 0:
            break

    if GetSetting("unknown_to_data", False, config) and len(arg_seg_name) > 0:
        if not len(arg_seg_name) == 0:
            ret.append(arg_seg_name)
    elif len(arg_seg_name) > 0:
        for char in arg_seg_name:
            ret.append("-" + char)

    return ret


def MatchDouble(arg_seg_name: str, config: dict) -> List[str]:
    ret = []

    arguments = ListArgumentsofType("--", config)

    found = True
    while len(arg_seg_name) > 0 and found:
        found = False

        for key in arguments:
            if len(key) > len(arg_seg_name):
                continue

            if arg_seg_name[0:len(key)] == key:
                ret.append("--" + arg_seg_name[0:len(key)])
                arg_seg_name = arg_seg_name[len(key):len(arg_seg_name)]
                found = True
                break

    if len(arg_seg_name) > 0 and GetSetting("unknown_to_data", False, config):
        ret.append(arg_seg_name)
    elif len(arg_seg_name) > 0:
        ret.append("--" + arg_seg_name)

    return ret


def MatchCommand(arg_seg_name: str, config: dict) -> List[str]:
    ret = []

    arguments = ListArgumentsofType("--", config)

    found = True
    while len(arg_seg_name) > 0 and found:
        found = False

        for key in arguments:
            if len(key) > len(arg_seg_name):
                continue

            if arg_seg_name[0:len(key)] == key:
                ret.append(arg_seg_name[0:len(key)])
                arg_seg_name = arg_seg_name[len(key):len(arg_seg_name)]
                found = True
                break

    if len(arg_seg_name) > 0:
        ret.append(arg_seg_name)

    return ret


def SplitArgumentSegments(arg: str, config: dict) -> List[str]:
    arg_type = GetArgType(arg)
    arg_name = GetArgName(arg)

    if arg_type == "-":
        if GetSetting("match-args", False, config):
            return MatchSingle(arg_name, config)
        else:
            ret = []

            for char in arg_name:
                ret.append("-" + char)

            return ret
    elif arg_type == "--":
        if GetSetting("match--args", False, config):
            return MatchDouble(arg_name, config)
        else:
            return [arg]
    elif arg_type == "command":
        if GetSetting("match_command_args", False, config):
            return MatchCommand(arg_name, config)
        else:
            return [arg]


def ProcessArguments(arguments: List[str], config: dict) -> List[str]:
    arguments.pop(0)

    # TODO Fix this ungodly madness (why tf did I do it like this?)
    new_arguments = []

    for argument in arguments:
        new_arguments += SplitSegments(argument)

    arguments = new_arguments
    new_arguments = []

    for argument in arguments:
        new_arguments += SplitArgumentSegments(argument, config)
    return new_arguments


def LoadJson(filename: str) -> dict:
    file = open(filename, "r")
    obj = json.load(file)
    file.close()
    return obj


def Parse(config: dict) -> List[dict]:
    arguments = ProcessArguments(sys.argv, config)
    print(arguments)

    parsed = []

    next = 0

    while True:
        if next >= len(arguments):
            break

        arg = FindArgs(next, arguments, config)

        parsed.append(arg)

        if "val" in arg:
            next += 1
        else:
            next += parsed[-1]["count"] + 1

    return parsed


print(Parse(LoadJson("./clap/clap.json")))
