"""
Core Chatbot Orchestrator for Task 06: AI Chatbot Application.

Coordinates NLP analysis, intent classification, multi-turn state management,
dynamic response generation, and optional external LLM routing.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.conversation_manager import ConversationManager
from src.llm_client import LLMClient
from src.models import ChatMessage, IntentMatch, current_time_str
from src.nlp_processor import NLPProcessor
from src.response_generator import ResponseGenerator
from src.web_search import WebSearchEngine


class Chatbot:
    """Intelligent conversational AI chatbot coordinating NLP, memory, and generation."""

    def __init__(
        self,
        nlp: Optional[NLPProcessor] = None,
        generator: Optional[ResponseGenerator] = None,
        conversation: Optional[ConversationManager] = None,
        llm: Optional[LLMClient] = None,
        web_search: Optional[WebSearchEngine] = None,
    ):
        """Initialize chatbot components."""
        self.nlp = nlp or NLPProcessor()
        self.generator = generator or ResponseGenerator(nlp=self.nlp)
        self.conversation = conversation or ConversationManager()
        self.llm = llm or LLMClient()
        self.web_search = web_search or WebSearchEngine()

    def process_message(self, user_text: str) -> ChatMessage:
        """Process incoming user message through NLP pipeline and return assistant response.

        Workflow:
            1. Normalize and extract sentiment.
            2. Classify intent and slots.
            3. Update conversation context (e.g. user name).
            4. Check for command triggers (clear/reset).
            5. Generate response via local NLP engine or external LLM.
            6. Store turns in dialogue history.
        """
        cleaned_text = user_text.strip()
        if not cleaned_text:
            return ChatMessage(
                role="assistant",
                content="I didn't catch anything! Please type a question or greeting.",
                intent="empty_input",
                confidence=1.0,
            )

        # 1. NLP Analysis: Sentiment & Normalization
        sentiment_res = self.nlp.analyze_sentiment(cleaned_text)

        # 2. Intent Classification & Slot Extraction
        search_query = self.nlp.detect_online_search(cleaned_text)
        if search_query:
            summary, source_url, engine_name = self.web_search.search_online(search_query)
            if summary:
                source_tag = f"\n\nSource: {source_url} ({engine_name})" if source_url else ""
                content = f"{summary}{source_tag}"
            else:
                content = f"I couldn't find live online information for '{search_query}'. Please try rephrasing."
            intent_match = IntentMatch(
                tag="online_search",
                confidence=0.95,
                slots={"query": search_query, "response": content},
            )
        else:
            intent_match = self.generator.classify_intent(
                cleaned_text,
                context=self.conversation.get_context(),
            )

        # 3. Handle Special Commands / Memory Operations
        if intent_match.tag == "clear_memory" or cleaned_text.lower() in ("clear", "reset", "clear history"):
            self.conversation.clear()
            reply_msg = ChatMessage(
                role="assistant",
                content="I've reset our conversation history and active memory! How can I assist you now?",
                intent="clear_memory",
                confidence=1.0,
                sentiment="neutral",
            )
            return reply_msg

        # Update context if name was extracted
        if intent_match.tag == "user_name_store" and "name" in intent_match.slots:
            extracted_name = intent_match.slots["name"]
            self.conversation.set_context_var("user_name", extracted_name)

        # Record User Message
        user_msg = ChatMessage(
            role="user",
            content=cleaned_text,
            timestamp=current_time_str(),
            intent=intent_match.tag,
            confidence=intent_match.confidence,
            sentiment=sentiment_res.sentiment,
            entities=intent_match.slots,
        )
        self.conversation.add_message(user_msg)

        # 4. Response Generation (Local vs External LLM)
        response_text = ""
        used_llm = False

        if intent_match.tag == "online_search" and "response" in intent_match.slots:
            response_text = intent_match.slots["response"]
        # If LLM is configured and intent is not a local utility (math/time/name), attempt LLM
        elif self.llm.is_configured() and intent_match.tag not in ("math_calc", "time_query", "user_name_store"):
            recent_turns = [
                {"role": m.role, "content": m.content}
                for m in self.conversation.get_messages()[-6:]
            ]
            llm_reply, err = self.llm.generate(recent_turns)
            if llm_reply:
                response_text = llm_reply
                used_llm = True
            else:
                # Fallback to local response generator on API failure
                response_text = self.generator.generate_response(
                    intent_match,
                    context=self.conversation.get_context(),
                )
        else:
            # Local NLP Engine response generation
            response_text = self.generator.generate_response(
                intent_match,
                context=self.conversation.get_context(),
            )

        # Record Assistant Message
        assistant_msg = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=current_time_str(),
            intent=intent_match.tag,
            confidence=intent_match.confidence,
            sentiment="neutral",
            entities={"used_llm": used_llm, **intent_match.slots},
        )
        self.conversation.add_message(assistant_msg)

        return assistant_msg

    def get_conversation_history(self) -> List[ChatMessage]:
        """Return full conversation message history."""
        return self.conversation.get_messages()

    def clear_conversation(self) -> None:
        """Clear conversation history and state."""
        self.conversation.clear()
