"""
Comprehensive unit and integration test suite for Task 06: NOVA AI Chatbot.

Tests NLP processing, intent classification, slot extraction, sentiment analysis,
safe mathematical evaluation, multi-turn conversation memory, external LLM mocking,
and headless GUI initialization.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chatbot import Chatbot
from src.conversation_manager import ConversationManager
from src.llm_client import LLMClient
from src.models import ChatMessage, IntentMatch, SentimentResult
from src.nlp_processor import NLPProcessor
from src.response_generator import ResponseGenerator, safe_eval_math


class TestNLPProcessor(unittest.TestCase):
    """Unit tests for NLP text normalization, tokenization, stemming, and sentiment."""

    def setUp(self):
        self.nlp = NLPProcessor()

    def test_expand_contractions(self):
        """Test expansion of colloquial English contractions."""
        self.assertEqual(self.nlp.expand_contractions("I don't think it's working"), "i do not think it is working")
        self.assertEqual(self.nlp.expand_contractions("can't and won't"), "cannot and will not")
        self.assertEqual(self.nlp.expand_contractions(""), "")

    def test_normalize_and_tokenize(self):
        """Test lowercase, punctuation stripping, and token extraction."""
        tokens = self.nlp.tokenize("Hello, World! How are you doing today?")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
        self.assertIn("today", tokens)
        self.assertNotIn(",", tokens)
        self.assertNotIn("!", tokens)

    def test_stem_word(self):
        """Test rule-based stemming of plural forms, gerunds, and adverbs."""
        self.assertEqual(self.nlp.stem_word("running"), "runn")
        self.assertEqual(self.nlp.stem_word("quickly"), "quick")
        self.assertEqual(self.nlp.stem_word("cats"), "cat")
        self.assertEqual(self.nlp.stem_word("development"), "develop")
        self.assertEqual(self.nlp.stem_word("hi"), "hi")  # Short word unchanged

    def test_preprocess_tokens(self):
        """Test tokenization with stopword filtering and stemming."""
        processed = self.nlp.preprocess_tokens("This is an amazing Python program for coding")
        self.assertNotIn("this", processed)
        self.assertNotIn("is", processed)
        self.assertNotIn("an", processed)
        self.assertNotIn("for", processed)
        self.assertTrue(len(processed) > 0)

    def test_similarity_metrics(self):
        """Test Jaccard and Cosine similarity computations."""
        # Jaccard
        tokens1 = ["python", "ai", "chatbot"]
        tokens2 = ["python", "ai", "internship"]
        j_score = self.nlp.jaccard_similarity(tokens1, tokens2)
        # 2 common (python, ai) out of 4 union (python, ai, chatbot, internship) = 0.5
        self.assertAlmostEqual(j_score, 0.5)

        # Cosine
        vec1 = {"python": 0.5, "ai": 0.5}
        vec2 = {"python": 0.5, "ai": 0.5}
        self.assertAlmostEqual(self.nlp.cosine_similarity(vec1, vec2), 1.0)

        vec_orth = {"ruby": 1.0}
        self.assertEqual(self.nlp.cosine_similarity(vec1, vec_orth), 0.0)

    def test_sentiment_analysis(self):
        """Test valence lexicon scoring and negation detection."""
        pos_result = self.nlp.analyze_sentiment("I had a great, fantastic, wonderful day!")
        self.assertEqual(pos_result.sentiment, "positive")
        self.assertGreater(pos_result.polarity, 0.2)

        neg_result = self.nlp.analyze_sentiment("This code is broken and terrible, I feel stressed.")
        self.assertEqual(neg_result.sentiment, "negative")
        self.assertLess(neg_result.polarity, -0.2)

        # Negation test: "not happy" should flip positive word to negative
        negated_res = self.nlp.analyze_sentiment("I am not happy with this error.")
        self.assertEqual(negated_res.sentiment, "negative")

    def test_extract_name(self):
        """Test user name extraction from greeting statements."""
        self.assertEqual(self.nlp.extract_name("My name is Rahul"), "Rahul")
        self.assertEqual(self.nlp.extract_name("I am Alice"), "Alice")
        self.assertEqual(self.nlp.extract_name("You can call me David"), "David")
        # Should not extract non-names
        self.assertIsNone(self.nlp.extract_name("I am tired"))
        self.assertIsNone(self.nlp.extract_name("Hello there"))

    def test_extract_math_expression(self):
        """Test detection and extraction of mathematical formulas."""
        self.assertEqual(self.nlp.extract_math_expression("calculate 45 * 12 + 100"), "45 * 12 + 100")
        self.assertEqual(self.nlp.extract_math_expression("what is 250 / 5"), "250 / 5")
        self.assertIsNone(self.nlp.extract_math_expression("what is python?"))


class TestResponseGenerator(unittest.TestCase):
    """Unit tests for AST mathematical evaluation, intent matching, and slot rendering."""

    def setUp(self):
        self.generator = ResponseGenerator()

    def test_safe_math_evaluation(self):
        """Test arithmetic evaluation and division by zero protection."""
        val, err = safe_eval_math("25 * 4 + 50")
        self.assertEqual(val, 150.0)
        self.assertIsNone(err)

        val_div, err_div = safe_eval_math("100 / 0")
        self.assertIsNone(val_div)
        self.assertIn("Division by zero", err_div)

        val_pow, err_pow = safe_eval_math("2 ** 8")
        self.assertEqual(val_pow, 256.0)

    def test_intent_classification(self):
        """Test matching known intents and fallback handling."""
        # Greeting
        match_greet = self.generator.classify_intent("hello there")
        self.assertEqual(match_greet.tag, "greeting")
        self.assertGreater(match_greet.confidence, 0.3)

        # Identity
        match_id = self.generator.classify_intent("who are you")
        self.assertEqual(match_id.tag, "identity")

        # Math
        match_math = self.generator.classify_intent("calculate 15 * 6")
        self.assertEqual(match_math.tag, "math_calc")
        self.assertIn("math_expression", match_math.slots)

    def test_dynamic_slot_filling(self):
        """Test response generation populates {name}, {time}, and {math_result}."""
        # Math slot
        math_match = IntentMatch(
            tag="math_calc",
            confidence=0.9,
            slots={"math_expression": "10 + 20"},
        )
        resp_math = self.generator.generate_response(math_match)
        self.assertIn("30", resp_math)

        # Name slot
        name_match = IntentMatch(
            tag="user_name_store",
            confidence=0.9,
            slots={"name": "Rahul"},
        )
        resp_name = self.generator.generate_response(name_match)
        self.assertIn("Rahul", resp_name)


class TestConversationManager(unittest.TestCase):
    """Unit tests for conversation state, history buffer, and file exports."""

    def setUp(self):
        self.manager = ConversationManager(max_history_turns=5)

    def test_add_and_truncate_history(self):
        """Test adding messages and capacity limits."""
        for i in range(7):
            msg = ChatMessage(role="user", content=f"Message {i}")
            self.manager.add_message(msg)

        # Should be truncated to max 5
        self.assertEqual(len(self.manager.get_messages()), 5)
        self.assertEqual(self.manager.context["turn_count"], 7)

    def test_context_variables_and_clear(self):
        """Test setting context variables and memory reset."""
        self.manager.set_context_var("user_name", "Priya")
        self.assertEqual(self.manager.get_context_var("user_name"), "Priya")

        self.manager.clear()
        self.assertIsNone(self.manager.get_context_var("user_name"))
        self.assertEqual(len(self.manager.get_messages()), 0)

    def test_export_json_and_txt(self):
        """Test exporting dialogue transcripts."""
        self.manager.add_message(ChatMessage(role="user", content="Hi"))
        self.manager.add_message(ChatMessage(role="assistant", content="Hello!"))

        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "chat.json"
            txt_file = Path(tmpdir) / "chat.txt"

            cnt_json = self.manager.export_to_json(json_file)
            self.assertEqual(cnt_json, 2)
            self.assertTrue(json_file.exists())

            cnt_txt = self.manager.export_to_txt(txt_file)
            self.assertEqual(cnt_txt, 2)
            self.assertTrue(txt_file.exists())


class TestChatbotOrchestrator(unittest.TestCase):
    """Integration tests for high-level Chatbot conversational flows."""

    def setUp(self):
        self.bot = Chatbot()

    def test_multi_turn_name_memory(self):
        """Test that bot stores user name and remembers it across turns."""
        reply1 = self.bot.process_message("My name is Rahul")
        self.assertEqual(reply1.intent, "user_name_store")
        self.assertIn("Rahul", reply1.content)

        # In turn 2, ask for name
        reply2 = self.bot.process_message("What is my name?")
        self.assertIn("Rahul", reply2.content)

    def test_math_calculation_pipeline(self):
        """Test math computation through process_message."""
        reply = self.bot.process_message("solve 50 * 4")
        self.assertEqual(reply.intent, "math_calc")
        self.assertIn("200", reply.content)

    def test_empty_input_handling(self):
        """Test sending whitespace returns courteous prompt."""
        reply = self.bot.process_message("   ")
        self.assertEqual(reply.intent, "empty_input")

    def test_clear_memory_command(self):
        """Test reset command resets conversation context."""
        self.bot.process_message("My name is Vikram")
        self.bot.process_message("clear")
        self.assertIsNone(self.bot.conversation.get_context_var("user_name"))


class TestLLMClient(unittest.TestCase):
    """Unit tests for LLM client configuration and error handling."""

    def test_unconfigured_client(self):
        """Test client reports not configured when key is missing or dummy."""
        client = LLMClient(api_key="")
        self.assertFalse(client.is_configured())

        dummy_client = LLMClient(api_key="your_api_key_here")
        self.assertFalse(dummy_client.is_configured())

    @patch("urllib.request.urlopen")
    def test_mocked_llm_response(self, mock_urlopen):
        """Test parsing valid response from mocked API."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"choices": [{"message": {"content": "Mocked LLM reply"}}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = LLMClient(api_key="sk-valid-mock-key-123456789")
        reply, err = client.generate([{"role": "user", "content": "Hello"}])
        self.assertEqual(reply, "Mocked LLM reply")
        self.assertIsNone(err)


class TestWebSearchEngine(unittest.TestCase):
    """Unit tests for live online web search and query cleaning."""

    def test_clean_query_prefixes(self):
        """Test stripping query prefixes."""
        from src.web_search import WebSearchEngine
        engine = WebSearchEngine()
        self.assertEqual(engine.clean_query("search online for Python 3.12"), "Python 3.12")
        self.assertEqual(engine.clean_query("who is Alan Turing?"), "Alan Turing")
        self.assertEqual(engine.clean_query("google Machine Learning"), "Machine Learning")

    def test_detect_online_search_patterns(self):
        """Test NLPProcessor search detection."""
        nlp = NLPProcessor()
        self.assertEqual(nlp.detect_online_search("search online for Quantum Computing"), "Quantum Computing")
        self.assertEqual(nlp.detect_online_search("latest news on Artificial Intelligence"), "Artificial Intelligence")
        self.assertIsNone(nlp.detect_online_search("hello there"))

    def test_chatbot_online_search_integration(self):
        """Test Chatbot processes search query and tags intent as online_search."""
        mock_search = MagicMock()
        mock_search.search_online.return_value = (
            "Python is a popular programming language.",
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "Wikipedia",
        )
        bot = Chatbot(web_search=mock_search)
        reply = bot.process_message("search online for Python")
        self.assertEqual(reply.intent, "online_search")
        self.assertIn("Python is a popular", reply.content)
        self.assertIn("Wikipedia", reply.content)


class TestGUIHeadless(unittest.TestCase):
    """Test GUI instantiation in headless environment."""

    def test_gui_creation_or_skip(self):
        """Test creating Chatbot GUI or skipping if display server is missing."""
        import tkinter as tk
        try:
            root = tk.Tk()
            root.withdraw()
            from src.gui import ChatbotGUI

            bot = Chatbot()
            gui = ChatbotGUI(root, bot)

            # Test quick prompt
            gui.entry_input.insert(0, "Hello")
            gui._on_send_message()

            self.assertEqual(len(bot.get_conversation_history()), 2)
            root.destroy()
        except tk.TclError:
            self.skipTest("Tkinter display server not available.")


if __name__ == "__main__":
    unittest.main()
