from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
    qdrant_path: str = ""
    collection_name: str = "docintel_chunks"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: str = "extractive"
    groq_api_key: str = ""
    google_api_key: str = ""
    mistral_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str = ""
    max_upload_mb: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
