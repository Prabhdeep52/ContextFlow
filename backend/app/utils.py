from datetime import datetime
from .config import PRICING

def log_info(message: str):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] INFO: {message}")

def log_error(message: str):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ERROR: {message}")

def count_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)

def calculate_cost(input_tokens: int, output_tokens: int, embedding_tokens: int = 0) -> float:
    return ((input_tokens / 1000) * PRICING["input_tokens_per_1k"] +
            (output_tokens / 1000) * PRICING["output_tokens_per_1k"] +
            (embedding_tokens / 1000) * PRICING["embedding_per_1k"])
