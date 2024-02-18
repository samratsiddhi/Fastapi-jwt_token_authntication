from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine
from sqlalchemy.ext.declarative import declarative_base

postgres_url = "postgresql://postgres:123@localhost/buddha"

engine = create_engine(postgres_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except:
        db.close()