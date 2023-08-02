from eventbot.infrastructure.config import Config


def build_dsn(config: Config = Config()) -> str:
    return f'postgresql://{config.database_user}:{config.database_password}' \
           f'@{config.database_host}:{config.database_port}/{config.database}'
