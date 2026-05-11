from tkinter import ttk
import tkinter as tk


class User:
    def __init__(self, id, username, name, password, privilege):
        self.username= username
        self.name = name
        self.id = id
        self.privilege = privilege
        self.password = password

    def get_username(self):
        return self.username
    
    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name
    
    def get_privilege(self):
        return self.privilege

    def get_password(self):
        return self.password
    
