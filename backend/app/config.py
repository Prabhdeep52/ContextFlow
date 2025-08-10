import os

# Use a mutable object to store the API key so it can be updated
class Config:
    def __init__(self):
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.CHAT_MODEL = "gemini-1.5-flash"
        self.EMBEDDING_MODEL = "models/embedding-001"
        self.TEMPERATURE = 0.1
        self.PRICING = {
            "input_tokens_per_1k": 0.0005,
            "output_tokens_per_1k": 0.0015,
            "embedding_per_1k": 0.0001
        }

# Global config instance
config = Config()

# Backward compatibility - expose as module-level variables
GOOGLE_API_KEY = config.GOOGLE_API_KEY
CHAT_MODEL = config.CHAT_MODEL
EMBEDDING_MODEL = config.EMBEDDING_MODEL
TEMPERATURE = config.TEMPERATURE
PRICING = config.PRICING
