"""Application configuration using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Valuation Workbench"
    environment: str = "dev"
    debug: bool = False
    log_level: str = "INFO"
    
    # GCP
    project_id: str
    region: str = "us-central1"
    
    # Database
    database_url: str
    db_echo: bool = False
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours
    
    # Storage
    uploads_bucket: str
    artifacts_bucket: str
    
    # BigQuery
    bq_dataset_raw: str
    bq_dataset_curated: str
    bq_dataset_valuation: str
    
    # Document AI
    document_ai_processor_id: str
    document_ai_location: str = "us"
    
    # Vertex AI
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-flash"
    
    # Pub/Sub
    pubsub_topic_ingestion: str
    pubsub_topic_validation: str
    
    # Cloud Tasks
    cloud_tasks_queue: str
    cloud_tasks_location: str = "us-central1"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

