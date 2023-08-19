from eventbot.infrastructure.persistence import drop_tables, get_database_engine, build_dsn

if __name__ == '__main__':
    drop_tables(get_database_engine(build_dsn()))
