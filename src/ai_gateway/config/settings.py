"""Settings for the AI Gateway."""
import os
from functools import lru_cache
from pathlib import Path
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class RoutingSettings(BaseSettings):
    strategy: str = Field(default="priority")
    fallback_enabled: bool = Field(default=True)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=2)
    health_check_interval_seconds: int = Field(default=30)


class RateLimitSettings(BaseSettings):
    enabled: bool = Field(default=True)
    default_rpm: int = Field(default=60)
    default_tpm: int = Field(default=100000)
    per_tenant: bool = Field(default=True)


class CacheSettings(BaseSettings):
    enabled: bool = Field(default=True)
    ttl_seconds: int = Field(default=300)
    max_entries: int = Field(default=1000)
    strategy: str = Field(default="semantic")


class BillingSettings(BaseSettings):
    enabled: bool = Field(default=True)
    track_per_tenant: bool = Field(default=True)
    track_per_model: bool = Field(default=True)
    cost_per_1k_input: dict[str, float] = Field(default_factory=lambda: {"anthropic": 0.003, "openai": 0.005})
    cost_per_1k_output: dict[str, float] = Field(default_factory=lambda: {"anthropic": 0.015, "openai": 0.015})


class APISettings(BaseSettings):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)


class LoggingSettings(BaseSettings):
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file: str = Field(default="logs/app.log")


class Settings(BaseSettings):
    routing: RoutingSettings = Field(default_factory=RoutingSettings)
    ratelimit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    billing: BillingSettings = Field(default_factory=BillingSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    model_config = {"env_prefix": "", "env_nested_delimiter": "__"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "development")
    config_dir = Path(__file__).parent.parent.parent.parent / "config"
    env_map = {"development": "dev", "production": "prod"}
    suffix = env_map.get(env, "")
    config_file = config_dir / f"application-{suffix}.yaml" if suffix else config_dir / "application.yaml"
    if not config_file.exists():
        config_file = config_dir / "application.yaml"
    cfg = {}
    if config_file.exists():
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
    return Settings(
        routing=RoutingSettings(**cfg.get("routing", {})) if cfg.get("routing") else RoutingSettings(),
        ratelimit=RateLimitSettings(**cfg.get("ratelimit", {})) if cfg.get("ratelimit") else RateLimitSettings(),
        cache=CacheSettings(**cfg.get("cache", {})) if cfg.get("cache") else CacheSettings(),
        billing=BillingSettings(**cfg.get("billing", {})) if cfg.get("billing") else BillingSettings(),
        api=APISettings(**cfg.get("api", {})) if cfg.get("api") else APISettings(),
        logging=LoggingSettings(**cfg.get("logging", {})) if cfg.get("logging") else LoggingSettings(),
    )
