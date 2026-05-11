import hashlib
from database.database import (
    selectUserByName,
    insertUser,
)
from classesFile import User

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def createUser(username, name, password, privilege):

    hashed_password = hash_password(password)
    insertUser(username, name, hashed_password, privilege)


def userLogin(username, password):

    userData = selectUserByName(username)
    user = User(userData[0][1], userData[0][2], userData[0][3], userData[0][4])

    if not user:
        return False

    input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    return input_hash == user.get_password()
