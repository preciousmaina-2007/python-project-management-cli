from __future__ import annotations

import re


EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(email: str) -> bool:
    """Return True if `email` looks like a valid email address.

    This uses a conservative regex sufficient for most lab use-cases and
    deliberately avoids external dependencies.
    """
    if not isinstance(email, str):
        return False
    return EMAIL_REGEX.fullmatch(email.strip()) is not None
