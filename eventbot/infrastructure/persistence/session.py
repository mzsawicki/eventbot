from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker


def get_session_factory(engine: Engine) -> sessionmaker:
    session_factory = sessionmaker(bind=engine)
    return session_factory
