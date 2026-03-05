from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_user:str
    db_name:str
    db_host:str
    db_password:str
    db_port: int

    access_secret_key: str
    access_token_expire_minutes: int
    refresh_secret_key: str
    refresh_token_expire_days: int
    algorithm: str

    class Config:
        env_file=".env"

settings=Settings()