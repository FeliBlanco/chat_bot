from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import os


load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ENGINE_IA: int = os.getenv("ENGINE_IA")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ASSISTANT_ID: str = os.getenv("ASSISTANT_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()