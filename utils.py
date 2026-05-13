import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def update_env_variable(key, value):
    lines = []
    found = False

    env_path = DIR_PATH + "/.env"

    with open(env_path, "r") as f:
        for line in f:
            if line.startswith(f"{key}="):
                lines.append(f"{key}=\"{value}\"\n")
                found = True
            else:
                lines.append(line)

    if not found:
        lines.append(f"{key}=\"{value}\"\n")

    with open(env_path, "w") as f:
        f.writelines(lines)
