import os
import pathlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Filesystem
    base_dir = pathlib.Path(__file__).parent.parent
    project_root = base_dir.parent

    # Database
    database = os.getenv('POSTGRES_DB')
    database_user = os.getenv('POSTGRES_USER')
    database_password = os.getenv('POSTGRES_PASSWORD')
    database_host = os.getenv('POSTGRES_HOST')
    database_port = int(os.getenv('POSTGRES_PORT'))

    # Discord
    token = os.getenv('DISCORD_TOKEN')
