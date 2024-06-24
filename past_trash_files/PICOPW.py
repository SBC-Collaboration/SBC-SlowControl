"""
This module provides functions to hash and verify passwords

By: Mathieu Laurin														

v1.0 Initial code 08/01/20 ML	
"""

import hashlib, binascii, os

def HashPW(Password):
    Salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    PWHash = hashlib.pbkdf2_hmac('sha512', Password.encode('utf-8'), Salt, 100000)
    PWHash = binascii.hexlify(PWHash)

    return (Salt + PWHash).decode('ascii')

def VerifyPW(StoredPassword, Password):
    Salt = StoredPassword[:64]
    StoredPassword = StoredPassword[64:]
    PWHash = hashlib.pbkdf2_hmac('sha512', Password.encode('utf-8'), Salt.encode('ascii'), 100000)
    PWHash = binascii.hexlify(PWHash).decode('ascii')

    return PWHash == StoredPassword
