from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb+srv://sujanat:sujan123@cluster0.w5he2fw.mongodb.net/"
    MONGODB_DB: str = "mydb"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",             # local dev
        "https://et-myfrontend.vercel.app",  # deployed frontend on Vercel
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
