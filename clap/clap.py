import sys
import json
from typing import List
from typing import Dict


def IsKnown(name: str, config: dict) -> bool:
    if "arguments" in config:
        if not name in config["arguments"]:
            return False
    else:
        return False
    return True


def IsDefaultSet(setting: str, config: dict) -> bool:
    if "default" in config:
        if setting in config["default"]:
            return True
    return False


def GetArgType(arg: str) -> str:
    dash_count = arg.count("-")
    arg_type = ""
    if dash_count == 2:
        arg_type = "--"
    elif dash_count == 1:
        arg_type = "-"

    elif dash_count > 2:
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
    if IsDefaultSet("count", config):
        arg_count = config["default"]["count"]

    return {"name": arg_name, "type": arg_type, "count": arg_count, "inferred": True}


def FindParameters(arg: str, config: dict) -> dict:
    name = arg.replace("-", "")

    if not IsKnown(name, config):
        return InferrParameters(arg, config)

    return {"name": name, "type": config["arguments"][name]["type"],
            "count": config["arguments"][name]["count"], "inferred": False}


def GetVal(val: str) -> dict:
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
            count += arg["args"][i]["count"]

    arg["count"] = count
    return arg


def Parse(config_filename: str) -> List[dict]:
    file = open(config_filename, "r")
    config = json.load(file)
    file.close()

    arguments = sys.argv
    arguments.pop(0)

    parsed = []

    next = 0

    while True:
        if next >= len(arguments):
            break

        args = FindArgs(next, arguments, config)

        parsed.append(args)

        next += parsed[len(parsed) - 1]["count"] + 1

    return parsed


print(Parse("clap.json"))
