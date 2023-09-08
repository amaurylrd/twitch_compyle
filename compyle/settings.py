import logging
from collections import namedtuple
from os import getenv

from dotenv import load_dotenv

load_dotenv()

# environment variables for the youtube service
YOUTUBE_CONFIG = namedtuple("YOUTUBE_APP_CONFIG", ["client_id", "client_secret", "redirect_uri", "client_email"])(
    getenv("YOUTUBE_APP_CLIENT_ID"),
    getenv("YOUTUBE_APP_CLIENT_SECRET"),
    getenv("YOUTUBE_APP_REDIRECT_URI", "http://localhost:3000/"),
    getenv("YOUTUBE_APP_EMAIL_ADDRESS"),
)

# environment variables for the twitch service
TWITCH_CONFIG = namedtuple("TWITCH_APP_CONFIG", ["client_id", "client_secret", "redirect_uri"])(
    getenv("TWITCH_APP_CLIENT_ID"),
    getenv("TWITCH_APP_CLIENT_SECRET"),
    getenv("TWITCH_APP_REDIRECT_URI", "http://localhost:3001/"),
)

# environment variables for the mongo database
MONGO_CONFIG = namedtuple("MONGO_DB_CONFIG", ["client_uri", "client_name"])(
    getenv("MONGO_DB_URI", "mongodb://localhost:27017/"),
    getenv("MONGO_DB_NAME", "compyle"),
)
