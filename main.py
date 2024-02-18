from sqlmodel import Session
from models import *
from database import get_db,engine
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, status
from hashing import *
from fastapi.security import OAuth2PasswordRequestForm
from schema import *
from utils import (
    create_access_token,
    create_refresh_token,
)
from deps import get_current_user,refresh_access_token

app = FastAPI()


def create_db_and_tables():
    SQLModel.metadata.create_all(bind=engine)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/users/")
def read_users():
    with Session(engine) as session:
        users = session.query(User).all()
        return users


@app.post('/signup', summary="Create new user", response_model=UserOut)
async def create_user(data: User, db: Session = Depends(get_db)):
    # querying database to check if user already exist
    user = db.query(User).filter(User.username == data.username).first()

    if user is not None:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail= "User with this username already exist"
        )

    new_user = User(
        id=data.id,
        username=data.username,
        password=get_password_hash(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == form_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not exist"
        )

    hashed_pass = user.password
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
    }


@app.post('/refresh', summary='Refresh access token for user', response_model=TokenSchema)
async def refresh_token(refresh_token: str, user: SystemUser = Depends(get_current_user)):
    tokens = await refresh_access_token(refresh_token, user.username)
    return tokens


@app.get('/me', summary='Get details of currently logged in user', response_model=UserOut)
async def get_me(user: SystemUser = Depends(get_current_user)):
    return user

