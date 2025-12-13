from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    api_base_url: str = "http://localhost:8000"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Telegram Bot Configuration
    telegram_bot_token: str
    telegram_admin_ids: str = ""
    
    # TikTok Configuration
    tiktok_cookie: str = ""
    tiktok_proxy: str = ""
    tiktok_headless: bool = True
    
    # Download Configuration
    download_path: str = "./downloads"
    max_concurrent_downloads: int = 3
    video_quality: str = "highest"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def admin_ids_list(self) -> list[int]:
        if not self.telegram_admin_ids:
            return []
        return [int(id.strip()) for id in self.telegram_admin_ids.split(",") if id.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
