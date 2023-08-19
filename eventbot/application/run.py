from eventbot.infrastructure.discord import run_bot
from eventbot.infrastructure.config import Config
from eventbot.infrastructure.persistence import SQLCalendarUnitOfWork, get_session_factory,\
    get_database_engine, build_dsn
from eventbot.infrastructure.time import LocalTimeClock

if __name__ == '__main__':
    config = Config()
    uow = SQLCalendarUnitOfWork(get_session_factory(get_database_engine(build_dsn(config))))
    run_bot(config.token, uow, LocalTimeClock())
