from clap import *
from pathlib import Path
import json
import os

clap_config_file = open(os.path.dirname(
    Path(__file__).absolute()) + "/template/clap-config.json", "r")
clap_config = json.load(clap_config_file)
clap_config_file.close()

arguments = Parse(clap_config)
print(arguments)

language = ""
template = ""


def EvalArgument(argument):
    if argument["name"] == "t" and argument["type"] == "-":
        pass
    elif argument["name"] == "l" and argument["type"] == "-":
        pass
