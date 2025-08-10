from typing import List
from datetime import datetime
import uuid

import sys
import os
from .models import ConversationEntry

class ConversationManager:
    """Manages conversation history"""
    
    def __init__(self):
        self.conversations: List[ConversationEntry] = []
    
    def add_conversation(self, entry: ConversationEntry):
        """Add a new conversation entry"""
        self.conversations.append(entry)
        # Keep only last 100 conversations
        if len(self.conversations) > 100:
            self.conversations = self.conversations[-100:]
    
    def get_conversation_history(self, limit: int = 10) -> List[ConversationEntry]:
        """Get conversation history"""
        return self.conversations[-limit:] if self.conversations else []
    
    def get_conversation_context(self, context_length: int = 3) -> str:
        """Get conversation context for enhanced retrieval"""
        recent = self.get_conversation_history(context_length)
        if not recent:
            return ""
        
        context = "Recent conversation context:\n"
        for conv in recent:
            context += f"Q: {conv.question}\nA: {conv.answer}\n\n"
        return context
    
    def search_conversations(self, query: str, limit: int = 10) -> List[ConversationEntry]:
        """Search through conversation history"""
        query_lower = query.lower()
        results = []
        
        for conv in reversed(self.conversations):
            if (query_lower in conv.question.lower() or 
                query_lower in conv.answer.lower()):
                results.append(conv)
                if len(results) >= limit:
                    break
        
        return results
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversations.clear()

conversation_manager = ConversationManager()