"""This module defines the configuration settings for the PayU Authentication Service using Pydantic's BaseSettings. The Settings class includes fields for database connection parameters, JWT token management, and allowed CORS origins. By using BaseSettings, we can easily load these configuration values from environment variables or a .env file, providing flexibility and security in managing sensitive information such as database credentials and secret keys. The settings instance is created at the end of the module, allowing other parts of the application to access the configuration values as needed."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """This class defines the configuration settings for the PayU Authentication Service. It includes fields for database connection parameters such as db_user, db_name, db_host, db_password, db_port, and db_url, which are essential for establishing a connection to the database. Additionally, it contains fields for JWT token management, including access_secret_key, access_token_expire_minutes, refresh_secret_key, refresh_token_expire_days, and algorithm, which are used for creating and verifying access and refresh tokens. The origins field is also included to specify allowed CORS origins for the API. By using Pydantic's BaseSettings, we can easily load these configuration values from environment variables or a .env file, providing flexibility and security in managing sensitive information such as database credentials and secret keys."""

    db_user: str
    db_name: str
    db_host: str
    db_password: str
    db_port: int
    db_url: str

    access_secret_key: str
    access_token_expire_minutes: int
    refresh_secret_key: str
    refresh_token_expire_days: int
    algorithm: str

    origins: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
