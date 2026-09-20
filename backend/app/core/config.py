from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "mock"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Google Gemini
    gemini_api_key: str = ""
    # Three free-tier Gemini models:
    #   gemini-2.0-flash-lite  — fastest, lowest cost
    #   gemini-1.5-flash       — balanced, generous free quota
    #   gemini-1.5-flash-8b    — smallest, highest free RPM
    gemini_model: str = "gemini-3.5-flash-lite"


settings = Settings()
