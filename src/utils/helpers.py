from fastapi import Depends, HTTPException,status,Request
import jwt
from jwt.exceptions import InvalidTokenError
from src.utils.settings import settings 
from sqlalchemy.orm import Session
from src.users.models import UserModel
from src.utils.db import get_db

def is_authenticated(request:Request, db:Session= Depends(get_db)):
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