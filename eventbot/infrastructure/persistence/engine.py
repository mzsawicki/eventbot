from sqlalchemy import create_engine, Engine


def get_database_engine(dsn: str) -> Engine:
    return create_engine(dsn)