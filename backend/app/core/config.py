from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os

# Build absolute path to .env file in the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH = os.path.join(BASE_DIR, '.env')

# Load the file explicitly
load_dotenv(dotenv_path=DOTENV_PATH)

class Settings(BaseSettings):
    DB_URL: str
    SECRET_KEY: str
    AGENT_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=DOTENV_PATH, env_file_encoding='utf-8')

@lru_cache()
def get_settings():
    return Settings()
