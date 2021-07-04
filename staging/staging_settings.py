# flake8: noqa
# pylint: skip-file
# type: ignore

from finanz.settings import *

DEBUG = bool(os.getenv("DJANGO_DEBUG", False))
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
# generate your own secret key using
# import random, string
# print("".join(random.choice(string.printable) for _ in range(50)))

# staticfiles
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
