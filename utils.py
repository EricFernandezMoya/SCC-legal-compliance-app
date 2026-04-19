import os

def clear_terminal():
    # 'nt' refers to Windows; 'posix' refers to Linux/macOS
    os.system('cls' if os.name == 'nt' else 'clear')
