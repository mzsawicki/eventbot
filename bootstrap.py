from eventbot.infrastructure.persistence import build_dsn, get_database_engine, map_tables, drop_tables


def bootstrap():
    engine = get_database_engine(build_dsn())
    drop_tables(engine)
    map_tables(engine)


if __name__ == '__main__':
    bootstrap()
