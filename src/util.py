
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from sqlmodel import Session
from .database import engine

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password):
    if password is None:
        return ""
    salt = bcrypt.gensalt()
    pw = bcrypt.hashpw(password.encode('utf-8'), salt)
    return pw.decode('utf-8')
