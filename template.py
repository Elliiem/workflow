import clap
from pathlib import Path
import json
import os


def Usage():
    print("Usage:")
    print("-l the language of the template")
    print("-t the template")
    print("-o the target directory (default == cwd)")

    exit()


def ApplyTemplate(target_path: str, template_path: str):
    if not any(os.listdir(template_path)):
        return

    os.system("cp -r {}/* {}".format(template_path, target_path))


clap_config_file = open(os.path.dirname(
    Path(__file__).absolute()) + "/template/clap-config.json", "r")
clap_config = json.load(clap_config_file)
clap_config_file.close()

arguments = clap.Parse(clap_config)

language = ""
template = ""
target = ""

for arg in arguments:
    if arg.arg == "-l":
        language = clap.GetValue(arg.args[0])

    if arg.arg == "-t":
        template = clap.GetValue(arg.args[0])

    if arg.arg == "-o":
        target = clap.GetValue(arg.args[0])


if template == "" or language == "":
    Usage()

template_path = "{}/template/{}/{}".format(os.path.dirname(
    Path(__file__).absolute()), language, template)

if not os.path.exists(template_path):
    print("Invalid Template!")
    Usage()

if not os.path.exists(target) and not target == "":
    print("Invalid Target!")
    Usage()


if not target == "":
    ApplyTemplate(target, template_path)
else:
    ApplyTemplate(os.getcwd(), template_path)
