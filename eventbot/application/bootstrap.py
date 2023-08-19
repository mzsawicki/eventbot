from eventbot.infrastructure.persistence import build_dsn, get_database_engine, map_tables


def bootstrap():
    engine = get_database_engine(build_dsn())
    map_tables(engine)


if __name__ == '__main__':
    bootstrap()
