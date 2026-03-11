import re

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def is_valid_instagram_username(value: str) -> bool:
    return bool(_USERNAME_PATTERN.fullmatch(value))
