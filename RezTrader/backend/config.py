from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RezTrader"
    API_V1_STR: str = "/api/v1"
    
    # Auth
    SECRET_KEY: str = "dev-secret-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./reztrader.db"  # Start simple
    
    # Trading
    PAPER_BALANCE: float = 1_000_000.0
    DEFAULT_SYMBOL: str = "BTCUSDT"
    
    class Config:
        env_file = ".env"

settings = Settings()