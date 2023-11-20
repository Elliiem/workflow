import sys
import json
from typing import List


def IsKnown(name: str, config: dict) -> bool:
    if "arguments" in config:
        if not name in config["arguments"]:
            return False
    else:
        return False
    return True


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


def GetArgType(arg: str) -> str:
    dash_count = arg.count("-")
    arg_type = ""
    if arg[1] == "-":
        arg_type = "--"
    elif dash_count == 1:
        arg_type = "-"
    elif dash_count > 0:
        arg_type = "---"
    else:
        arg_type = "command"

    return arg_type


def GetArgName(arg: str) -> str:
    return arg.replace("-", "")


def InferrParameters(arg: str, config: dict) -> dict:
    arg_name = GetArgName(arg)
    arg_type = GetArgType(arg)

    arg_count = 0
    if IsSettingSet("default_count", config):
        arg_count = config["settings"]["default_count"]

    return {"name": arg_name, "type": arg_type, "count": arg_count, "inferred": True}


def FindParameters(arg: str, config: dict) -> dict:
    name = arg.replace("-", "")

    if not IsKnown(name, config):
        return InferrParameters(arg, config)

    return {"name": name, "type": config["arguments"][name]["type"],
            "count": config["arguments"][name]["count"], "inferred": False}


def GetVal(val: str) -> dict:
    if val.lstrip('-').isdigit():
        return {"type": "number", "val": val}

    return {"type": "string", "val": val}


def FindArgs(arg_index: int, arguments: List[str], config: dict) -> dict:
    if arg_index >= len(arguments):
        return {}
    parameters = FindParameters(arguments[arg_index], config)

    arg = {"name": GetArgName(
        arguments[arg_index]), "type": GetArgType(arguments[arg_index]), "args": []}

    count = 0

    for i in range(1, parameters["count"] + 1):
        if arg_index + i >= len(arguments):
            break
        if IsKnown(arguments[arg_index + i], config):
            arg["args"].append(
                FindArgs(arg_index + i, arguments, config))
        else:
            arg["args"].append(GetVal(arguments[arg_index + i]))
            count += 1

    for i in range(0, len(arg["args"])):
        if "count" in arg["args"][i]:
            print(count)
            count += arg["args"][i]["count"]

    arg["count"] = count

    if parameters["inferred"]:
        arg["known"] = False
    else:
        arg["known"] = True

    return arg


def SplitSegments(segments: str) -> List[str]:
    arg_type = GetArgType(segments)
    if not arg_type == "---":
        return [segments]

    cur = segments.find("-", 0)

    split = []
    print(cur)

    while not cur == -1:
        next = segments.find("-", cur + 2)

        if next == -1:
            print(segments[cur:len(segments)])
            split.append(segments[cur:len(segments)])
        else:
            print(segments[cur:next])
            split.append(segments[cur:next])

        cur = next

    print(split)
    return split


def Match(arg: str, type: str, config: dict) -> List[str]:
    raise Exception("Match() is not implemented!")


def SplitArguments(arg: str, config: dict) -> List[str]:
    arg_type = GetArgType(arg)

    if arg_type == "-":
        do_match = GetSetting("match-args", False, config)

        if do_match:
            return Match(arg, arg_type, config)
        else:
            arg_name = GetArgName(arg)
            args = []

            for char in arg_name:
                args.append("-" + char)

            return args
    elif arg_type == "--":
        do_match = GetSetting("match--args", False, config)

        if do_match:
            return Match(arg, arg_type, config)
        else:
            return [arg]
    elif arg_type == "command":
        do_match = GetSetting("match_command_args", False, config)

        if do_match:
            return Match(arg, arg_type, config)
        else:
            return [arg]


def ProcessArguments(arguments: List[str], config: dict) -> List[str]:
    arguments.pop(0)

    new_arguments = []
    for argument in arguments:
        new_arguments += SplitSegments(argument)
    arguments = new_arguments
    new_arguments = []

    for argument in arguments:
        new_arguments += SplitArguments(argument, config)
    return new_arguments


def Parse(config: dict) -> List[dict]:
    arguments = ProcessArguments(sys.argv, config)

    parsed = []
    next = 0

    while True:
        if next >= len(arguments):
            break

        args = FindArgs(next, arguments, config)

        parsed.append(args)

        next += parsed[len(parsed) - 1]["count"] + 1

    return parsed
