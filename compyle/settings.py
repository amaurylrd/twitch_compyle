from os import getenv
from dotenv import load_dotenv

load_dotenv()

# environment variables for the youtube service
YOUTUBE = {
    "client_id": getenv("YOUTUBE_APP_CLIENT_ID"),
    "client_secret": getenv("YOUTUBE_APP_CLIENT_SECRET"),
    "redirect_uri": getenv("YOUTUBE_APP_REDIRECT_URI", "http://localhost"),
    "client_email": getenv("YOUTUBE_APP_EMAIL_ADDRESS"),
}

# environment variables for the twitch service
TWITCH = {
    "client_id": getenv("TWITCH_APP_CLIENT_ID"),
    "client_secret": getenv("TWITCH_APP_CLIENT_SECRET"),
    "redirect_uri": getenv("TWITCH_APP_REDIRECT_URI", "http://localhost"),
}
