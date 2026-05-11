import bcrypt
from database.database import (
    selectUserByName,
    insertUser,
)
from classesFile import User

def hash_password(password):

    password_bytes = password.encode('utf-8')

    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return hashed_password.decode('utf-8')


def createUser(username, name, password, privilege):

    hashed_password = hash_password(password)
    insertUser(username, name, hashed_password, privilege)


def userLogin(username, password):
   
    userData = selectUserByName(username)
    user = User(userData[0][0], userData[0][1], userData[0][2], userData[0][3], userData[0][4])
    
    if not user:
        return False
        
    stored_hash = user.get_password().encode('utf-8')

    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
