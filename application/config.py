import pydantic

__all__ = ["config"]


class Config(pydantic.BaseSettings):
    telegram_token: str
    mongo_dsn: str = "mongodb://mongo:27017"
    log_level: str = "INFO"

    clam_host: str = "clamd-api"
    clam_port: int = 3000
    clam_key: str = "FILES"

    @property
    def clam_url(self) -> str:
        return f"http://{self.clam_host}:{self.clam_port}"

    class Config:
        case_sensitive = False
        env_file_encoding = "utf-8"
        env_prefix = "app_"


config = Config()
