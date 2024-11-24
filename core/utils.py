import re


def validate_username(username: str) -> bool:
    """
    Validates if the username is alphanumeric (including dot), starts with a letter,
    and is at least 3 characters long.
    """
    pattern = r"^[a-zA-Z][a-zA-Z0-9.]{2,}$"
    return bool(re.match(pattern, username))


def validate_password(password: str) -> bool:
    """
    Validates if the password is at least 4 characters long.
    All characters are allowed.
    """
    pattern = r"^.{4,}$"  # At least 4 characters, any characters allowed
    return bool(re.match(pattern, password))
