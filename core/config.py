from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int

    # MEDIAMTX_API_URL: str
    # # MEDIAMTX_API_USERNAME: str
    # # MEDIAMTX_API_PASSWORD: str
    # MEDIAMTX_RTSP_PORT: int
    # MEDIAMTX_HTTP_PORT: int
    # MEDIAMTX_RTMP_PORT: int
    # MEDIAMTX_HOST: str

    SECRET_KEY: str

    # DATABASE_URL: str


settings = Settings()
