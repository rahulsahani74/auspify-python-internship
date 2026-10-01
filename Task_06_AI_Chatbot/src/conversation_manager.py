"""
Conversation State and Dialogue History Manager for the NOVA Chatbot.

Tracks multi-turn context, user variables (name, topic, sentiment history),
and handles conversation export and memory resets.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models import ChatMessage


class ConversationManager:
    """Manages dialogue history, active conversation state, and contextual memory."""

    def __init__(self, max_history_turns: int = 100):
        """Initialize empty conversation state and history buffer."""
        self.max_history_turns = max_history_turns
        self.messages: List[ChatMessage] = []
        self.context: Dict[str, Any] = {
            "user_name": None,
            "current_topic": None,
            "turn_count": 0,
            "sentiment_history": [],
        }

    def add_message(self, message: ChatMessage) -> None:
        """Append a dialogue turn to history buffer, truncating if over capacity."""
        self.messages.append(message)
        if len(self.messages) > self.max_history_turns:
            self.messages.pop(0)

        if message.role == "user":
            self.context["turn_count"] = self.context.get("turn_count", 0) + 1
            # Track sentiment history
            if message.sentiment:
                s_hist = self.context.setdefault("sentiment_history", [])
                s_hist.append(message.sentiment)
                if len(s_hist) > 10:
                    s_hist.pop(0)

    def get_messages(self) -> List[ChatMessage]:
        """Return full dialogue history list."""
        return list(self.messages)

    def get_context(self) -> Dict[str, Any]:
        """Return active conversational context dictionary."""
        return dict(self.context)

    def set_context_var(self, key: str, value: Any) -> None:
        """Update an active context variable."""
        self.context[key] = value

    def get_context_var(self, key: str, default: Any = None) -> Any:
        """Retrieve value of a context variable."""
        return self.context.get(key, default)

    def clear(self) -> None:
        """Reset conversation messages and context state."""
        self.messages.clear()
        self.context = {
            "user_name": None,
            "current_topic": None,
            "turn_count": 0,
            "sentiment_history": [],
        }

    def export_to_json(self, filepath: Path | str) -> int:
        """Save conversation history to a JSON file.

        Returns:
            Number of saved messages.
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "context": self.context,
            "messages": [m.to_dict() for m in self.messages],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return len(self.messages)

    def export_to_txt(self, filepath: Path | str) -> int:
        """Export readable conversation transcript to a text file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: List[str] = [
            "=" * 60,
            "  NOVA AI CHATBOT — CONVERSATION TRANSCRIPT",
            "=" * 60,
            f"User: {self.context.get('user_name') or 'Anonymous'}",
            f"Total Messages: {len(self.messages)}",
            "-" * 60,
            "",
        ]
        for m in self.messages:
            author = "USER" if m.role == "user" else "NOVA (AI)"
            lines.append(f"[{m.timestamp}] {author}:")
            lines.append(f"  {m.content}")
            lines.append("")
        lines.append("=" * 60)

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return len(self.messages)
