from os import getenv
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

# environment variables for the youtube service
YOUTUBE_APP: Dict[str, Optional[str]] = {
    "client_id": getenv("YOUTUBE_APP_CLIENT_ID"),
    "client_secret": getenv("YOUTUBE_APP_CLIENT_SECRET"),
    "redirect_uri": getenv("YOUTUBE_APP_REDIRECT_URI", "http://localhost:3000/"),
    "client_email": getenv("YOUTUBE_APP_EMAIL_ADDRESS"),
}

# environment variables for the twitch service
TWITCH_APP: Dict[str, Optional[str]] = {
    "client_id": getenv("TWITCH_APP_CLIENT_ID"),
    "client_secret": getenv("TWITCH_APP_CLIENT_SECRET"),
    "redirect_uri": getenv("TWITCH_APP_REDIRECT_URI", "http://localhost:3001/"),
}

# environment variables for the mongo database
MONGO_DB: Dict[str, Optional[str]] = {
    "client_uri": getenv("MONGO_DB_URI", "mongodb://localhost:27017/"),
}
