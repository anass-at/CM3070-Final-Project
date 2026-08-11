from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "identity_db"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    HYDRA_ADMIN_URL: str = "http://localhost:4445"
    HYDRA_PUBLIC_URL: str = "http://localhost:4444"

    MAIL_HOST: str = "localhost"
    MAIL_PORT: int = 1025
    MAIL_FROM: str = "NatID <noreply@natid.local>"
    FRONTEND_URL: str = "http://localhost:5500"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
