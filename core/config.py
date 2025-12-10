from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    MEDIAMTX_API: str
    MEDIAMTX_STREAM: str
    SECRET_KEY: str
    HOST_IP_FOR_CLIENT: str
settings = Settings()
