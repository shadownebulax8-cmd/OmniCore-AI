"""
Conversation context memory for maintaining session-based chat history.
Uses Redis to store conversation context per session ID.
"""
import json
import time
import uuid
from typing import List, Dict, Optional
import redis
from config.settings import settings


class ConversationContext:
    """Manage conversation context for multi-turn dialogues."""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.max_history_length = settings.CONVERSATION_MAX_HISTORY_LENGTH
        self.session_ttl = settings.CONVERSATION_SESSION_TTL_SECONDS
    
    def create_session(self) -> str:
        """Create a new conversation session and return session ID."""
        session_id = str(uuid.uuid4())
        self.redis.setex(f"session:{session_id}", self.session_ttl, json.dumps([]))
        return session_id
    
    def add_exchange(self, session_id: str, question: str, answer: str, 
                     escalated: bool = False) -> None:
        """Add a question-answer exchange to the conversation history."""
        history_key = f"session:{session_id}"
        
        # Get existing history
        history_json = self.redis.get(history_key)
        if history_json:
            history = json.loads(history_json)
        else:
            history = []
        
        # Add new exchange
        exchange = {
            "question": question,
            "answer": answer,
            "escalated": escalated,
            "timestamp": time.time()
        }
        history.append(exchange)
        
        # Trim to max length
        if len(history) > self.max_history_length:
            history = history[-self.max_history_length:]
        
        # Save back to Redis with extended TTL
        self.redis.setex(history_key, self.session_ttl, json.dumps(history))
    
    def get_context(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        history_key = f"session:{session_id}"
        history_json = self.redis.get(history_key)
        
        if not history_json:
            return []
        
        return json.loads(history_json)
    
    def get_formatted_context(self, session_id: str) -> str:
        """Get formatted conversation context for LLM consumption."""
        history = self.get_context(session_id)
        
        if not history:
            return ""
        
        formatted = []
        for exchange in history:
            formatted.append(f"Q: {exchange['question']}")
            formatted.append(f"A: {exchange['answer']}")
        
        return "\n".join(formatted)
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self.redis.delete(f"session:{session_id}")
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self.redis.exists(f"session:{session_id}") > 0


# Global instance
conversation_context = ConversationContext()
