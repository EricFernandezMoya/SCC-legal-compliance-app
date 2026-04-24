class User:
    def __init__(self, username, name, password, privilege):
        self.username= username
        self.name = name
        self.password = password
        self.privilege = privilege

    def get_username(self):
        return self.username
    
    def get_password(self):
        return self.password
    
    def get_name(self):
        return self.name
    
    def get_privilege(self):
        self.privilege