import sys
from typing import List


class Argument:
    def __init__(self, arg: str, args) -> None:
        self.arg = arg
        self.args = args


class ArgumentInfo:
    def __init__(self, arg: str, count: int, known: bool) -> None:
        self.arg = arg
        self.count = count
        self.known = known


class Value:
    def __init__(self, val: str) -> None:
        self.value = val.lstrip('-')
        self.value = self.value.lstrip('~')

        if self.value.isdigit():
            self.value = int(self.value)


def _IsKnown(arg: str, config: dict) -> bool:
    name = _GetArgName(arg)
    type = _GetArgType(arg)

    if "arguments" in config:
        if arg in config["arguments"]:
            return True

    return False


def _IsSettingSet(setting: str, config: dict) -> bool:
    if "settings" in config:
        if setting in config["settings"]:
            return True
    return False


def _GetSetting(setting: str, default: any, config: dict) -> any:
    if _IsSettingSet(setting, config):
        return config["settings"][setting]
    else:
        return default


def _GetArgType(arg: str) -> str:
    dash_count = arg.count("-")

    if arg.count("~") > 0:
        return "data"

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


def _GetArgName(arg: str) -> str:
    ret = arg.replace("~", "")
    return ret.replace("-", "")


def _GetArgumentInfo(arg: str, config: dict) -> dict:
    name = _GetArgName(arg)
    type = _GetArgType(arg)

    if type == "data":
        return Value(name)

    if not _IsKnown(arg, config):
        return ArgumentInfo(arg, _GetSetting("default_count", 0, config), False)
    else:
        return ArgumentInfo(arg, config["arguments"][arg]["count"], True)


def _FindArgs(arg_index: int, arguments: List[str], config: dict) -> dict:
    if arg_index >= len(arguments):
        return Argument("", []), 0

    info = _GetArgumentInfo(arguments[arg_index], config)

    if type(info) == Value:
        return info, 1

    arg = Argument(info.arg, [])

    count = 0

    for i in range(1, info.count + 1):
        if arg_index + i >= len(arguments):
            break

        if _IsKnown(arguments[arg_index + i], config):
            arg_r, count_r = _FindArgs(arg_index + i, arguments, config)

            arg.args.append(arg_r)

            count += count_r + 1
        else:
            arg.args.append(Value(arguments[arg_index + i]))
            count += 2

    return arg, count


def _GetCharacterRunLenght(input: str, index: int) -> int:
    if index >= len(input):
        return 0
    if index == len(input) - 1:
        return 1

    target_char = input[index]

    i = index + 1

    run = 1

    while True:
        if i >= len(input):
            break

        if not input[i] == target_char:
            break

        run += 1
        i += 1

    return run


def _SplitSegment(segment: str) -> List[str]:
    cur = 0

    ret = []

    while not cur == -1:
        next = segment.find("-", cur + _GetCharacterRunLenght(segment, cur))

        if next == -1:
            ret.append(segment[cur:len(segment)])
        else:
            ret.append(segment[cur:next])

        cur = next

    return ret


def _ListArgumentsofType(type: str, config: dict) -> List[str]:
    if not "arguments" in config:
        return []

    ret = []
    for key in config["arguments"]:
        if _GetArgType(key) == type:
            ret.append(_GetArgName(key))

    return ret


def _MatchSingle(name: str, config: dict) -> List[str]:
    ret = []

    while _IsKnown("-" + name[0], config):
        ret.append("-" + name[0])
        name = name[1:len(name)]
        if len(name) == 0:
            break

    if _GetSetting("unknown_to_data", False, config) and len(name) > 0:
        if not len(name) == 0:
            ret.append("~" + name)
    elif len(name) > 0:
        for char in name:
            ret.append("-" + char)

    return ret


def _MatchDouble(name: str, config: dict) -> List[str]:
    ret = []

    arguments = _ListArgumentsofType("--", config)

    found = True
    while len(name) > 0 and found:
        found = False

        for key in arguments:
            if len(key) > len(name):
                continue

            if name[0:len(key)] == key:
                ret.append("--" + name[0:len(key)])
                name = name[len(key):len(name)]
                found = True
                break

    if len(name) > 0 and _GetSetting("unknown_to_data", False, config):
        ret.append("~" + name)
    elif len(name) > 0:
        ret.append("--" + name)

    return ret


def _MatchCommand(name: str, config: dict) -> List[str]:
    ret = []

    arguments = _ListArgumentsofType("command", config)

    found = True
    while len(name) > 0 and found:
        found = False

        for key in arguments:
            if len(key) > len(name):
                continue

            if name[0:len(key)] == key:
                ret.append(name[0:len(key)])
                name = name[len(key):len(name)]
                found = True
                break

    if len(name) > 0 and _GetSetting("unknown_to_data", False, config):
        ret.append("~" + name)
    elif len(name) > 0:
        ret.append(name)

    return ret


def _MatchSegment(arg: str, config: dict) -> List[str]:
    arg_type = _GetArgType(arg)
    arg_name = _GetArgName(arg)

    if arg_type == "-":
        if _GetSetting("match-args", False, config):
            return _MatchSingle(arg_name, config)
        else:
            ret = []

            for char in arg_name:
                ret.append("-" + char)

            return ret
    elif arg_type == "--":
        if _GetSetting("match--args", False, config):
            return _MatchDouble(arg_name, config)
        else:
            return [arg]
    elif arg_type == "command":
        if _GetSetting("match_command_args", False, config):
            return _MatchCommand(arg_name, config)
        else:
            return [arg]

    return []


def _ProcessArguments(arguments: List[str], config: dict) -> List[str]:
    arguments.pop(0)

    for i in range(0, len(arguments)):
        arguments[i:i + 1] = _SplitSegment(arguments[i])

    for i in range(0, len(arguments)):
        arguments[i:i + 1] = _MatchSegment(arguments[i], config)

    return arguments


def Parse(config: dict) -> List[dict]:
    arguments = _ProcessArguments(sys.argv, config)

    parsed = []

    next = 0

    while True:
        if next >= len(arguments):
            break

        arg, count = _FindArgs(next, arguments, config)

        next += count

        parsed.append(arg)

    return parsed


def GetValue(val: Value) -> any:
    if type(val) == Value:
        return val.value
    else:
        return ""
