
from datetime import datetime
from typing import Any, Dict


class MemoryStore:
    """Stores metrics and session data"""
    
    def __init__(self):
        self.total_tokens_processed = 0
        self.total_cost = 0.0
        self.session_start = datetime.now()
    
    def add_metrics(self, tokens: int, cost: float):
        """Add metrics to the store"""
        self.total_tokens_processed += tokens
        self.total_cost += cost
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        return {
            "session_duration": session_duration,
            "total_tokens_processed": self.total_tokens_processed,
            "total_cost": self.total_cost,
            "tokens_per_minute": (self.total_tokens_processed / (session_duration / 60)) if session_duration > 0 else 0
        }

memory_store = MemoryStore()