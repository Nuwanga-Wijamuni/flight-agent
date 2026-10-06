from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    flight_provider: Literal['demo', 'duffel_test'] = 'demo'
    duffel_access_token: str = ''
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    database_url: str = 'sqlite:///./flight_agent.db'
    cors_origin: str = 'http://localhost:5173'


settings = Settings()
