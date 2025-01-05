import datetime as dt
import yaml
from functools import lru_cache

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class TelloConfig(BaseModel):
    email: str
    password: str
    card_expiration: dt.date

    @field_validator("card_expiration", mode="before")
    @classmethod
    def check_card_expiration(cls, value: str) -> dt.date:
        formats = [
            "%m/%y",
            "%m-%y",
            "%m/%Y",
            "%m-%Y",
            "%m/%d/%y",
            "%m-%d-%y",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m",
            "%Y-%m-%d",
        ]

        for f in formats:
            try:
                return dt.datetime.strptime(value, f).date()
            except ValueError:
                pass
        raise ValueError(f"Unknown expiration date format {value}")


class SmtpConfig(BaseModel):
    server: str
    port: int
    username: str
    password: str
    from_email: str


class Config(BaseSettings):
    tello: TelloConfig
    smtp: SmtpConfig

    class Config:
        env_nested_delimiter = "__"


@lru_cache
def get_settings() -> Config:
    with open("config/config.yaml", "r") as config_yaml:
        return Config(**yaml.safe_load(config_yaml))
