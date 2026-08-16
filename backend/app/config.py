from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./canteen.db"
    jwt_secret: str = "change-this-to-a-long-random-secret"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    canteen_open_hour: int = 8
    canteen_close_hour: int = 20
    max_item_quantity: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
