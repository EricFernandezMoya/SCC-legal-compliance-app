import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

def update_env_variable(key, value):
    lines = []
    found = False

    env_path = DIR_PATH + "/.env"

    # Read existing .env
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith(f"{key}="):
                lines.append(f"{key}=\"{value}\"\n")
                found = True
            else:
                lines.append(line)

    # If variable not found, append it
    if not found:
        lines.append(f"{key}=\"{value}\"\n")

    # Write back to .env
    with open(env_path, "w") as f:
        f.writelines(lines)


