from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DZ identity
    dz_id: str = "2351"
    dz_tz: str = "Europe/Madrid"
    dz_lat: float = 37.16
    dz_lon: float = -5.61

    # Scraper
    burble_base_url: str = "https://dzm.burblesoft.eu"

    # Storage
    video_storage_path: str = "/mnt/ssd/videos"
    sd_card_watch_path: str = "/media"

    # Database
    database_url: str = "sqlite+aiosqlite:////data/skybox.db"


settings = Settings()
