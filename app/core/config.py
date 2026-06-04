from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cassandra_host: str = "127.0.0.1"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "financial_dwh"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()