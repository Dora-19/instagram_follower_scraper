from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class FollowerResult:
    username: str
    followers: Optional[int]
    success: bool
    attempts: int
    elapsed_ms: int
    error: Optional[str] = None
