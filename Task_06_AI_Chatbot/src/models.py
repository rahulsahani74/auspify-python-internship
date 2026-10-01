"""
Data models and representations for the NOVA AI Chatbot.

Defines ChatMessage, IntentMatch, SentimentResult, and serialization utilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def current_time_str() -> str:
    """Return local time formatted as 'HH:MM:SS'."""
    return datetime.now().strftime("%H:%M:%S")


def current_date_str() -> str:
    """Return current date formatted as 'YYYY-MM-DD'."""
    return datetime.now().strftime("%Y-%m-%d")


def current_timestamp_str() -> str:
    """Return current timestamp formatted as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class SentimentResult:
    """Result of lexical sentiment analysis.

    Attributes:
        polarity: Score between -1.0 (extremely negative) and +1.0 (extremely positive).
        sentiment: Category ('positive', 'neutral', 'negative').
    """

    polarity: float
    sentiment: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "polarity": round(self.polarity, 3),
            "sentiment": self.sentiment,
        }


@dataclass
class IntentMatch:
    """Result of intent classification and pattern matching.

    Attributes:
        tag: Identified intent name (e.g. 'greeting', 'math_calc').
        confidence: Matching score between 0.0 and 1.0.
        matched_pattern: Knowledge base pattern with highest similarity.
        slots: Extracted named entities and context values.
    """

    tag: str
    confidence: float
    matched_pattern: str = ""
    slots: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tag": self.tag,
            "confidence": round(self.confidence, 3),
            "matched_pattern": self.matched_pattern,
            "slots": self.slots,
        }


@dataclass
class ChatMessage:
    """A single conversational dialogue message.

    Attributes:
        role: Message author ('user', 'assistant', 'system').
        content: Text content of the dialogue.
        timestamp: Time string when message occurred.
        intent: Classified intent tag if applicable.
        confidence: Classification confidence score.
        sentiment: Sentiment classification if evaluated.
        entities: Dict of extracted entities or computational slots.
    """

    role: str
    content: str
    timestamp: str = field(default_factory=current_time_str)
    intent: Optional[str] = None
    confidence: float = 0.0
    sentiment: str = "neutral"
    entities: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "intent": self.intent,
            "confidence": round(self.confidence, 3),
            "sentiment": self.sentiment,
            "entities": self.entities,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Reconstruct ChatMessage from dictionary."""
        return cls(
            role=data.get("role", "assistant"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", current_time_str()),
            intent=data.get("intent"),
            confidence=float(data.get("confidence", 0.0)),
            sentiment=data.get("sentiment", "neutral"),
            entities=data.get("entities", {}),
        )
