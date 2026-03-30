import random
import string
from datetime import datetime, timezone


def generate_order_number() -> str:
    """Generate a unique order number like FORM-2026-A7X9K2."""
    now = datetime.now(timezone.utc)
    year = now.year
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"FORM-{year}-{suffix}"
