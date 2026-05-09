from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Target service
    SEARCH_SERVICE_URL: str = "http://localhost:8003"
    SEARCH_SERVICE_TIMEOUT: int = 30

    # This service
    EVAL_SERVICE_HOST: str = "0.0.0.0"
    EVAL_SERVICE_PORT: int = 8010
    EVAL_SERVICE_RELOAD: bool = False
    EVAL_SERVICE_LOG_LEVEL: str = "info"

    # OpenAI — used by RAGAS for metric computation (not proxied through local gateway)
    OPENAI_API_KEY: str
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "ragops-retrieval-eval"


settings = Settings()
