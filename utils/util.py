import os
import pathlib
import re
import subprocess

def exec(command, app_repo=".", return_output=False):
    command = command.split()
    command_process = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=app_repo)
    command_output = command_process.stdout.read().decode()
    if return_output:
        return command_output
    else:
        print(command_output)


def get_home_dir():
    p_dir = pathlib.Path(os.getcwd()).resolve().parent.parent.parent

    print(p_dir)
    return p_dir


pattern = '^(\.+)'
def remove_first_dots(text):
    after = re.sub(pattern, '', text)
    return after

if __name__ == "__main__":
    content = r'a....MainAct.python...aaa'
    print(content)
    print(remove_first_dots(content))

