import bcrypt
from database import *

def hash_password(password):

    password_bytes = password.encode('utf-8')

    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    return hashed_password.decode('utf-8')


def createUser():

    username = input("User name: ")
    password = input("password: ")

    hashed_password = hash_password(password)

    user = {"username": username, "password": hashed_password}

    return user


def userLogin(username, password):
   
    user = selectUser(username)
    if not user:
        print("User doesn't exist")
        return False
        
    stored_hash = user["password"].encode('utf-8')

    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

