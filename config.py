from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "GeeksForGeeks Stats API"
    app_description: str = "An API for analyzing GeeksForGeeks user problem-solving statistics"
    app_version: str = "1.0.0"
    
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    request_timeout: float = 10.0

settings = Settings()
