import bcrypt
from database import *
from classesFile import User

def hash_password(password):

    password_bytes = password.encode('utf-8')

    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return hashed_password.decode('utf-8')


def createUser(username, name, password, privilege):

    hashed_password = hash_password(password)
    insertUser(username, name, hashed_password, privilege)


def userLogin(username, password):
   
    user = selectUser(username)
    if not user:
        print("User doesn't exist")
        return False
        
    stored_hash = user.get_password().encode('utf-8')

    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# createUser("eryczek", "Eric Fernandez Moya", "210885", "ADMIN")