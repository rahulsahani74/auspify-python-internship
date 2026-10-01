"""
Natural Language Processing (NLP) Engine for the NOVA Chatbot.

Provides text normalization, contraction expansion, tokenization,
stopword filtering, rule-based stemming, TF-IDF cosine similarity,
sentiment classification, and entity/slot extraction without external dependencies.
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.models import SentimentResult


# Standard English contractions mapping
CONTRACTIONS: Dict[str, str] = {
    "i'm": "i am",
    "i'll": "i will",
    "i'd": "i would",
    "i've": "i have",
    "you're": "you are",
    "you'll": "you will",
    "you'd": "you would",
    "you've": "you have",
    "he's": "he is",
    "she's": "she is",
    "it's": "it is",
    "we're": "we are",
    "they're": "they are",
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "aren't": "are not",
    "isn't": "is not",
    "wasn't": "was not",
    "weren't": "were not",
    "that's": "that is",
    "what's": "what is",
    "who's": "who is",
    "there's": "there is",
    "let's": "let us",
}

# Curated English stop words
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "during", "before", "after", "above", "below",
    "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "each", "few", "more", "most", "other", "some",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "doing", "at", "by", "for", "with", "about",
    "against", "between", "into", "through"
}

# Lexicon for Sentiment Polarity
POSITIVE_WORDS: Set[str] = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic", "awesome",
    "happy", "glad", "joy", "love", "loved", "delighted", "superb", "brilliant",
    "pleased", "excited", "fun", "enjoy", "enjoyed", "best", "cool", "helpful",
    "terrific", "positive", "productive", "inspiring", "motivated", "enthusiastic"
}

NEGATIVE_WORDS: Set[str] = {
    "bad", "terrible", "awful", "horrible", "sad", "unhappy", "angry", "hate",
    "hated", "stressed", "stressful", "depressed", "frustrated", "frustrating",
    "annoyed", "annoying", "tired", "exhausted", "broken", "bug", "bugs", "error",
    "failed", "failure", "fail", "useless", "confused", "stuck", "overwhelmed", "worst"
}

NEGATION_WORDS: Set[str] = {
    "not", "never", "no", "hardly", "barely", "scarcely", "cannot", "n't"
}


class NLPProcessor:
    """Natural Language Processing engine for text processing, tokenization, and similarity."""

    def __init__(self, stop_words: Optional[Set[str]] = None):
        """Initialize the NLP processor with optional custom stopwords."""
        self.stop_words = stop_words if stop_words is not None else STOP_WORDS

    def expand_contractions(self, text: str) -> str:
        """Expand colloquial English contractions (e.g. "don't" -> "do not")."""
        if not text:
            return ""
        lowered = text.lower()
        for cont, expanded in CONTRACTIONS.items():
            lowered = re.sub(r"\b" + re.escape(cont) + r"\b", expanded, lowered)
        return lowered

    def normalize(self, text: str) -> str:
        """Normalize text: expand contractions, lowercase, strip punctuation and extra spaces."""
        if not text:
            return ""
        expanded = self.expand_contractions(text)
        # Keep alphanumeric, math operators (+-*/%^), and spaces
        cleaned = re.sub(r"[^\w\s\+\-\*\/\%\^\.]", " ", expanded)
        return re.sub(r"\s+", " ", cleaned).strip()

    def tokenize(self, text: str) -> List[str]:
        """Split normalized text into word tokens."""
        normalized = self.normalize(text)
        if not normalized:
            return []
        return re.findall(r"\b\w+\b", normalized)

    def stem_word(self, word: str) -> str:
        """Lightweight rule-based morphological stemmer.

        Strips common inflectional suffixes while preserving core roots.
        """
        w = word.lower().strip()
        if len(w) <= 3:
            return w

        # Common suffix stripping
        for suffix in ("sses", "ies"):
            if w.endswith(suffix):
                return w[:-len(suffix)] + "i"
        for suffix in ("ing", "ed", "ly", "ment", "ness", "tion", "able", "ible"):
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                return w[:-len(suffix)]
        if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            return w[:-1]

        return w

    def preprocess_tokens(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """Tokenize, optionally filter stopwords, and stem tokens."""
        tokens = self.tokenize(text)
        processed: List[str] = []
        for t in tokens:
            if remove_stopwords and t in self.stop_words:
                continue
            stemmed = self.stem_word(t)
            if stemmed:
                processed.append(stemmed)
        return processed

    # --- Similarity & Scoring ---

    def jaccard_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Compute Jaccard similarity coefficient between two token collections."""
        set1 = set(tokens1)
        set2 = set(tokens2)
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute Term Frequency (TF) for a token list."""
        tf_dict: Dict[str, float] = {}
        if not tokens:
            return tf_dict
        total = len(tokens)
        for t in tokens:
            tf_dict[t] = tf_dict.get(t, 0.0) + (1.0 / total)
        return tf_dict

    def cosine_similarity(
        self,
        vec1: Dict[str, float],
        vec2: Dict[str, float],
    ) -> float:
        """Compute cosine similarity between two sparse term weight vectors."""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(val * vec2.get(term, 0.0) for term, val in vec1.items())
        norm1 = math.sqrt(sum(val * val for val in vec1.values()))
        norm2 = math.sqrt(sum(val * val for val in vec2.values()))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot_product / (norm1 * norm2)

    # --- Sentiment Analysis ---

    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Compute sentiment polarity (-1.0 to +1.0) and category.

        Accounts for positive/negative keywords, booster words, and negation windows.
        """
        tokens = self.tokenize(text)
        if not tokens:
            return SentimentResult(polarity=0.0, sentiment="neutral")

        score = 0.0
        words_scored = 0
        negated = False

        for i, token in enumerate(tokens):
            # Check negation window of 2 preceding words
            if any(prev in NEGATION_WORDS for prev in tokens[max(0, i - 2) : i]):
                negated = True
            else:
                negated = False

            if token in POSITIVE_WORDS:
                score += -1.0 if negated else 1.0
                words_scored += 1
            elif token in NEGATIVE_WORDS:
                score += 1.0 if negated else -1.0
                words_scored += 1

        if words_scored == 0:
            polarity = 0.0
        else:
            polarity = max(-1.0, min(1.0, score / max(1, words_scored)))

        if polarity >= 0.2:
            sentiment = "positive"
        elif polarity <= -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return SentimentResult(polarity=polarity, sentiment=sentiment)

    # --- Entity & Slot Extraction ---

    def extract_name(self, text: str) -> Optional[str]:
        """Extract user name from phrases like 'my name is Rahul' or 'i am John'."""
        patterns = [
            r"\bmy name is ([A-Za-z]+)\b",
            r"\bi am called ([A-Za-z]+)\b",
            r"\bcall me ([A-Za-z]+)\b",
            r"\bthis is ([A-Za-z]+)\b",
            r"\bi am ([A-Za-z]+)\b",
        ]
        lowered = text.strip()
        for p in patterns:
            match = re.search(p, lowered, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Ignore non-names like 'sad', 'happy', 'fine', 'tired', 'doing'
                if candidate.lower() not in (
                    "sad", "happy", "fine", "tired", "good", "doing",
                    "learning", "coding", "here", "ready", "interested"
                ):
                    return candidate.capitalize()
        return None

    def extract_math_expression(self, text: str) -> Optional[str]:
        """Detect and extract mathematical expression for computation."""
        # Clean prefix keywords like 'calculate', 'solve', 'what is'
        cleaned = re.sub(
            r"^(calculate|solve|evaluate|compute|what is the result of|what is)\s+",
            "",
            text.strip(),
            flags=re.IGNORECASE,
        )
        cleaned = cleaned.rstrip("? .!")

        # Match expressions like "45 * 12 + 100", "(10 + 5) / 3", "2 ** 8"
        pattern = r"^[\d\.\s\+\-\*\/\%\^\(\)]+$"
        if re.match(pattern, cleaned) and any(op in cleaned for op in "+-*/%^"):
            # Ensure at least two numbers are present
            numbers = re.findall(r"\d+", cleaned)
            if len(numbers) >= 2 or ("^" in cleaned or "**" in cleaned):
                return cleaned.strip()

        return None

    def detect_online_search(self, text: str) -> Optional[str]:
        """Detect if user query explicitly requests an online web search.

        Returns:
            Extracted search topic if detected, None otherwise.
        """
        lowered = text.strip()
        search_patterns = [
            r"^(?:search\s+(?:the\s+web\s+|online\s+)?(?:for\s+)?|google\s+)(.+)$",
            r"^(?:online\s+data\s+(?:about|for)|live\s+data\s+for|latest\s+(?:news|info)\s+on)\s+(.+)$",
            r"^(?:find\s+online\s+(?:info|information)\s+on|look\s+up\s+online|look\s+up)\s+(.+)$",
        ]
        for p in search_patterns:
            m = re.match(p, lowered, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip("?.!")
        return None
