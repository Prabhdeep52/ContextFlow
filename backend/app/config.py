import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHAT_MODEL = "gemini-1.5-flash"
EMBEDDING_MODEL = "models/embedding-001"
TEMPERATURE = 0.1

PRICING = {
    "input_tokens_per_1k": 0.0005,
    "output_tokens_per_1k": 0.0015,
    "embedding_per_1k": 0.0001
}
