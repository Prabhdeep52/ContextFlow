from .config import GOOGLE_API_KEY

def configure_api_key(api_key: str):
    global GOOGLE_API_KEY
    GOOGLE_API_KEY = api_key

def is_api_key_configured():
    return GOOGLE_API_KEY is not None and GOOGLE_API_KEY.strip() != ""
