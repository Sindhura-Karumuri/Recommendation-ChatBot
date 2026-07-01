"""
Conversational SHL Assessment Recommender Agent.
"""
import json
import logging
import re
from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL
from backend.prompts import SYSTEM_PROMPT, REFUSAL_PATTERNS, OFF_TOPIC_RESPONSE
from backend.services.retrieval import build_catalog_context
from backend.services.catalog import get_by_name
from backend.services.comparator import compare

logger = logging.getLogger(__name__)

# Singleton Groq client — instantiated once, reused across requests
_client: Groq | None = None

# Patterns that indicate a query is too vague to recommend without clarification
_VAGUE_PATTERNS = [
    r"^i need an? assessment\.?$",
    r"^assessment\.?$",
    r"^help\.?$",
    r"^test\.?$",
    r"^hiring\.?$",
    r"^i want to hire\.?$",
]


def _get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set.")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _is_off_topic(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in REFUSAL_PATTERNS)


def _is_vague(text: str) -> bool:
    t = text.lower().strip()
    return any(re.fullmatch(p, t) for p in _VAGUE_PATTERNS)


def _turn_count(messages: list[dict]) -> int:
    return sum(1 for m in messages if m["role"] == "user")


def _retrieval_query(messages: list[dict]) -> str:
    # Use full conversation window (spec cap: 8 turns = 16 messages max)
    return " ".join(m["content"] for m in messages[-16:] if m["role"] in ("user", "assistant"))


def _parse_llm_response(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*", "", text).strip().strip("`").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"reply": text, "recommendations": [], "end_of_conversation": False}


def _validate_recs(recs: list) -> list:
    validated = []
    for r in recs:
        name = (r.get("name") or "").strip()
        url = (r.get("url") or "").strip()
        test_type = (r.get("test_type") or "").strip()

        if not (url and "shl.com" in url and "product-catalog" in url):
            item = get_by_name(name)
            if not item:
                continue
            url = item["url"]
            if not test_type and item.get("test_types"):
                test_type = item["test_types"][0]

        if not test_type:
            item = get_by_name(name)
            test_type = (item.get("test_types") or ["K"])[0] if item else "K"

        validated.append({"name": name, "url": url, "test_type": test_type})

    return validated[:10]


def _extract_comparison_names(messages: list[dict]) -> list[str]:
    """Extract previously recommended assessment names from conversation history."""
    names = []
    for m in reversed(messages):
        if m["role"] == "assistant":
            found = re.findall(r'"([^"]{3,60})"', m["content"])
            names.extend(found)
        if len(names) >= 4:
            break
    return names[:4]


def chat(messages: list[dict]) -> dict:
    if not messages:
        return {
            "reply": (
                "Hi! I'm the SHL Assessment Recommender. Tell me about the role "
                "you're hiring for and I'll suggest suitable assessments from the catalog."
            ),
            "recommendations": [],
            "end_of_conversation": False,
        }

    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

    if _is_off_topic(last_user):
        return {"reply": OFF_TOPIC_RESPONSE, "recommendations": [], "end_of_conversation": False}

    turn = _turn_count(messages)
    query = _retrieval_query(messages)
    catalog_ctx = build_catalog_context(query, k=20)

    # Inject comparison data if user is comparing
    comparison_ctx = ""
    if re.search(r"\bcompare\b|\bdifference\b|\bvs\.?\b", last_user, re.I):
        names = _extract_comparison_names(messages)
        if len(names) >= 2:
            comparison_ctx = "\n\n" + compare(names)

    turn_note = ""
    if turn >= 5:
        turn_note = (
            f"\n[SYSTEM NOTE: Turn {turn}/8. Commit to recommendations now "
            "unless critically under-specified.]"
        )

    # Spec cap: max 8 turns = max 16 messages; pass all within that window
    llm_messages = [
        {"role": "system", "content": SYSTEM_PROMPT + turn_note},
        {"role": "system", "content": catalog_ctx + comparison_ctx},
    ]
    for m in messages[-16:]:
        llm_messages.append({"role": m["role"], "content": m["content"]})

    response = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=llm_messages,
        temperature=0.1,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    parsed = _parse_llm_response(response.choices[0].message.content or "")
    reply = str(parsed.get("reply") or "")
    recs = parsed.get("recommendations") or []
    eoc = bool(parsed.get("end_of_conversation", False))

    # Suppress recommendations on vague queries
    if _is_vague(last_user):
        recs = []
    if recs:
        recs = _validate_recs(recs)
    if eoc and not reply:
        reply = "I hope these recommendations are helpful. Good luck with your hiring!"

    return {"reply": reply, "recommendations": recs, "end_of_conversation": eoc}
