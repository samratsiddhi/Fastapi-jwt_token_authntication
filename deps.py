from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils import (
    ALGORITHM,
    JWT_SECRET_KEY,
    JWT_REFRESH_SECRET_KEY,
    create_access_token
)
from models import User
from jose import jwt
from pydantic import ValidationError
from schema import TokenPayload, SystemUser
from database import get_db

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/login",scheme_name="JWT")


async def get_current_user(token: str = Depends(reuseable_oauth)) -> SystemUser:
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db = next(get_db())
    user = db.query(User).filter(User.username == token_data.sub).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return SystemUser(id=user.id, username=user.username, password=user.password)


async def refresh_access_token(refresh_token : str, username:str):
    try:
        payload = jwt.decode(
            refresh_token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db = next(get_db())
    user = db.query(User).filter(User.username == token_data.sub).first()
    if user.username == username:
        access_token = create_access_token(username)
        return {
            "access_token": create_access_token(username),
            "refresh_token": refresh_token
        }

