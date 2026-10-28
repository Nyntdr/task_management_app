from src.users.schemas import LoginSchema, UserSchema
from sqlalchemy.orm import Session
from src.users.models import UserModel
from fastapi import HTTPException,status,Request
from pwdlib import PasswordHash
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError
from src.utils.settings import settings

password_hash=PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def register(body: UserSchema, db:Session):
    is_user = db.query(UserModel).filter(UserModel.username == body.username).first()
    if is_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists.")

    email_exists = db.query(UserModel).filter(UserModel.email == body.email).first()
    if email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address already exists.")

    hash_password = get_password_hash(body.password)

    new_user = UserModel(
        name=body.name,
        username=body.username,
        email=body.email,
        hash_password=hash_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(body:LoginSchema ,db:Session):
    is_user = db.query(UserModel).filter(UserModel.username == body.username).first()
    if not is_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username is not correct.")   

    if not verify_password(body.password, is_user.hash_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Password is wrong.")
    
    exp_time= datetime.now()+ timedelta(minutes=settings.EXP_TIME)
    token=jwt.encode({"_id":is_user.id, "exp":exp_time.timestamp()},settings.SECRET_KEY,settings.ALGORITHM)
     
    return { "token":token}



def is_authenticated(request:Request, db:Session):
    try: 
        token=request.headers.get("Authorization")

        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")
    
        data=jwt.decode(token.split(" ")[-1],settings.SECRET_KEY,algorithms=[settings.ALGORITHM])

        user_id=data.get("_id")
    
        is_user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not is_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized.")   
    
        return is_user

    except InvalidTokenError:           
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")