"""
Response Generation Engine for the NOVA Chatbot.

Implements TF-IDF semantic pattern matching, safe mathematical evaluation,
dynamic slot filling, and fallback handling.
"""

import ast
import json
import math
import operator as op
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.models import IntentMatch, current_date_str, current_time_str
from src.nlp_processor import NLPProcessor


# Supported mathematical operators for AST safe evaluation
SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_eval_math(expression: str) -> Tuple[Optional[float], Optional[str]]:
    """Safely evaluate mathematical expressions using the Python AST parser.

    Does NOT use eval() to prevent arbitrary code execution vulnerabilities.
    """
    clean_expr = expression.replace("^", "**").strip()

    def _eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Constant):  # Python 3.8+ numeric literals
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                    raise ZeroDivisionError("Division by zero is undefined.")
                # Prevent massive exponents that would cause DoS
                if op_type == ast.Pow and (right > 1000 or left > 10000):
                    raise OverflowError("Exponent value exceeds safe limit.")
                return SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"Operator {op_type.__name__} is not permitted.")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            raise ValueError(f"Unary operator {op_type.__name__} is not permitted.")
        else:
            raise ValueError(f"Unsupported syntax in expression.")

    try:
        parsed = ast.parse(clean_expr, mode="eval")
        result = _eval_node(parsed.body)
        return result, None
    except ZeroDivisionError as err:
        return None, str(err)
    except OverflowError as err:
        return None, str(err)
    except Exception as err:
        return None, f"Could not evaluate expression: {err}"


class ResponseGenerator:
    """Matches intents and generates contextual, dynamic responses."""

    def __init__(
        self,
        knowledge_base_path: Optional[Path | str] = None,
        nlp: Optional[NLPProcessor] = None,
        confidence_threshold: float = 0.30,
    ):
        """Initialize generator with knowledge base data and NLP processor."""
        self.nlp = nlp or NLPProcessor()
        self.confidence_threshold = confidence_threshold
        self.intents: List[Dict[str, Any]] = []
        self.pattern_index: List[Dict[str, Any]] = []
        self.idf_dict: Dict[str, float] = {}

        kb_path = (
            Path(knowledge_base_path)
            if knowledge_base_path
            else Path(__file__).resolve().parent.parent / "data" / "knowledge_base.json"
        )
        self.load_knowledge_base(kb_path)

    def load_knowledge_base(self, path: Path) -> None:
        """Load intent schemas and compute TF-IDF index across training patterns."""
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.intents = data.get("intents", [])
        self._build_index()

    def _build_index(self) -> None:
        """Precompute tokenized vectors and IDF dictionary for fast similarity."""
        self.pattern_index.clear()
        doc_freq: Dict[str, int] = {}
        total_docs = 0

        for intent in self.intents:
            tag = intent.get("tag", "")
            for pattern in intent.get("patterns", []):
                tokens = self.nlp.preprocess_tokens(pattern, remove_stopwords=False)
                if not tokens:
                    continue
                total_docs += 1
                unique_tokens = set(tokens)
                for t in unique_tokens:
                    doc_freq[t] = doc_freq.get(t, 0) + 1

                tf_vec = self.nlp.compute_tf(tokens)
                self.pattern_index.append({
                    "tag": tag,
                    "pattern": pattern,
                    "tokens": tokens,
                    "tf": tf_vec,
                })

        # Calculate IDF: log(1 + N / (1 + df))
        self.idf_dict = {
            term: math.log(1.0 + (total_docs / (1.0 + df)))
            for term, df in doc_freq.items()
        }

        # Apply TF-IDF weights to pattern index
        for entry in self.pattern_index:
            tfidf_vec: Dict[str, float] = {}
            for term, tf in entry["tf"].items():
                tfidf_vec[term] = tf * self.idf_dict.get(term, 1.0)
            entry["tfidf"] = tfidf_vec

    def classify_intent(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> IntentMatch:
        """Identify the best-matching intent and confidence score for user text."""
        ctx = context or {}

        # 1. Check for Math Expression Calculation
        math_expr = self.nlp.extract_math_expression(user_text)
        if math_expr:
            return IntentMatch(
                tag="math_calc",
                confidence=0.95,
                matched_pattern="calculate",
                slots={"math_expression": math_expr},
            )

        # 2. Check for User Name Introduction
        name = self.nlp.extract_name(user_text)
        if name:
            return IntentMatch(
                tag="user_name_store",
                confidence=0.92,
                matched_pattern="my name is",
                slots={"name": name},
            )

        # 3. TF-IDF Cosine Similarity Matching
        query_tokens = self.nlp.preprocess_tokens(user_text, remove_stopwords=False)
        if not query_tokens:
            return IntentMatch(tag="fallback", confidence=0.0)

        query_tf = self.nlp.compute_tf(query_tokens)
        query_tfidf = {
            t: tf * self.idf_dict.get(t, 1.0) for t, tf in query_tf.items()
        }

        best_score = 0.0
        best_tag = "fallback"
        best_pattern = ""

        for entry in self.pattern_index:
            score = self.nlp.cosine_similarity(query_tfidf, entry["tfidf"])
            # Bonus for exact or substring match
            clean_query = self.nlp.normalize(user_text)
            clean_pattern = self.nlp.normalize(entry["pattern"])
            if clean_query == clean_pattern:
                score = 1.0
            elif clean_pattern in clean_query or clean_query in clean_pattern:
                score = max(score, 0.75)

            if score > best_score:
                best_score = score
                best_tag = entry["tag"]
                best_pattern = entry["pattern"]

        # Jaccard verification if cosine is borderline
        if best_score < self.confidence_threshold:
            for entry in self.pattern_index:
                j_score = self.nlp.jaccard_similarity(query_tokens, entry["tokens"])
                if j_score > best_score:
                    best_score = j_score
                    best_tag = entry["tag"]
                    best_pattern = entry["pattern"]

        if best_score >= self.confidence_threshold:
            return IntentMatch(
                tag=best_tag,
                confidence=best_score,
                matched_pattern=best_pattern,
            )

        return IntentMatch(tag="fallback", confidence=best_score)

    def generate_response(
        self,
        intent_match: IntentMatch,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render response template with populated dynamic slots."""
        ctx = context or {}
        tag = intent_match.tag

        # Find intent responses
        intent_def = next((i for i in self.intents if i.get("tag") == tag), None)
        templates = intent_def.get("responses", []) if intent_def else []

        if not templates:
            templates = [
                "I understand your message, but I don't have a specific response prepared. How else can I assist you?"
            ]

        chosen_template = random.choice(templates)

        # Dynamic Slot Population
        # 1. Math calculation
        if tag == "math_calc" and "math_expression" in intent_match.slots:
            expr = intent_match.slots["math_expression"]
            val, err = safe_eval_math(expr)
            if err:
                return f"Math computation error: {err}"
            # Format integer nicely without .0 if whole number
            if val is not None and val.is_integer():
                formatted_val = f"{int(val):,}"
            else:
                formatted_val = f"{val:,.4f}" if val is not None else "0"
            return chosen_template.format(math_result=f"{expr} = {formatted_val}")

        # 2. Name store or query
        current_name = intent_match.slots.get("name") or ctx.get("user_name")
        if "{name}" in chosen_template:
            if current_name:
                chosen_template = chosen_template.format(name=current_name)
            else:
                if tag == "user_name_query":
                    return "You haven't told me your name yet! You can say 'My name is [your name]' and I will remember it."
                chosen_template = chosen_template.format(name="friend")

        # 3. Time / Date queries
        if "{time}" in chosen_template or "{date}" in chosen_template:
            now = datetime.now()
            time_str = now.strftime("%I:%M:%S %p")
            date_str = now.strftime("%A, %B %d, %Y")
            chosen_template = chosen_template.format(time=time_str, date=date_str)

        return chosen_template
