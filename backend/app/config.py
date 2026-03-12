from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SMTP (env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, etc.)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
