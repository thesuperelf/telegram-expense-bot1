import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Config:
    bot_token: str
    database_url: str


def load_config() -> Config:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not bot_token:
        raise ValueError("Переменная окружения BOT_TOKEN не задана.")
    if not database_url:
        raise ValueError("Переменная окружения DATABASE_URL не задана.")

    return Config(bot_token=bot_token, database_url=database_url)
