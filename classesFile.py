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

class Document:
    def __init__(self, document_id, name, jurisdiction, year, description, date_created, date_updated, document_type):
        self.document_id = document_id
        self.name = name
        self.jurisdiction = jurisdiction
        self.year = year
        self.description = description
        self.date_created = date_created
        self.date_updated = date_updated
        self.document_type = document_type
    
    def getId(self):
        return self.document_id