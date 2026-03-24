from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Scraper
    burble_base_url: str = "https://burble.com"
    burble_poll_interval_minutes: int = 2

    # Storage
    video_storage_path: str = "/mnt/ssd/videos"
    sd_card_watch_path: str = "/media"

    # Database
    database_url: str = "sqlite+aiosqlite:////data/skybox.db"


settings = Settings()
