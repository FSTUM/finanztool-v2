# flake8: noqa
# pylint: skip-file
# type: ignore

import random
import string

from finanz.settings import *


def get_random_secret() -> str:
    letters = string.printable
    return "".join(random.choice(letters) for _ in range(50))  # nosec: This is a staging fallback


DEBUG = bool(os.getenv("DJANGO_DEBUG", False))
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret())
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
