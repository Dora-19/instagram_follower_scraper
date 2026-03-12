import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    provider: str = "instaloader"
    instagram_username: str = ""
    instagram_password: str = ""
    session_file: str = ".session-instaloader"
    max_concurrency: int = 5
    requests_per_minute: int = 30
    max_retries: int = 3
    backoff_base_seconds: float = 2.0
    browserbase_cdp_url: str = ""
    browserbase_profile_url_template: str = "https://www.instagram.com/{username}/"
    browserbase_timeout_ms: int = 30000

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            provider=os.getenv("PROVIDER", "instaloader"),
            instagram_username=os.getenv("INSTAGRAM_USERNAME", ""),
            instagram_password=os.getenv("INSTAGRAM_PASSWORD", ""),
            session_file=os.getenv("INSTAGRAM_SESSION_FILE", ".session-instaloader"),
            max_concurrency=int(os.getenv("MAX_CONCURRENCY", "5")),
            requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            backoff_base_seconds=float(os.getenv("BACKOFF_BASE_SECONDS", "2")),
            browserbase_cdp_url=os.getenv("BROWSERBASE_CDP_URL", ""),
            browserbase_profile_url_template=os.getenv(
                "BROWSERBASE_PROFILE_URL_TEMPLATE", "https://www.instagram.com/{username}/"
            ),
            browserbase_timeout_ms=int(os.getenv("BROWSERBASE_TIMEOUT_MS", "30000")),
        )

    @property
    def session_path(self) -> Path:
        return Path(self.session_file).expanduser().resolve()
