from configparser import ConfigParser
from sqlmodel import Session, SQLModel, create_engine
from models import *

alembic_ini = ConfigParser()
alembic_ini.read("alembic.ini")

connect_args = {"check_same_thread": False}
engine = create_engine(
    alembic_ini.get("alembic", "sqlalchemy.url"),
    connect_args=connect_args,
)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
