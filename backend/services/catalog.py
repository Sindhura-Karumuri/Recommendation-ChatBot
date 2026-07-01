"""
Loads and indexes the SHL catalog.
Uses BM25 + TF-IDF hybrid search with reciprocal rank fusion.
"""
import json
import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.config import CATALOG_PATH

_catalog: list[dict] = []
_bm25: BM25Okapi | None = None
_tfidf_matrix = None
_tfidf: TfidfVectorizer | None = None
_docs: list[str] = []
_name_index: dict[str, int] = {}


def _make_doc(item: dict) -> str:
    parts = [item.get("name", "")]
    if desc := item.get("description", ""):
        parts.append(desc)
    if labels := item.get("test_type_labels", []):
        parts.append("Type: " + " ".join(labels))
    if levels := item.get("job_levels", []):
        parts.append("Levels: " + " ".join(levels))
    if langs := item.get("languages", []):
        parts.append("Languages: " + " ".join(langs))
    if dur := item.get("duration", ""):
        parts.append(f"Duration {dur}")
    return " ".join(parts)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def load_and_index() -> None:
    global _catalog, _bm25, _tfidf_matrix, _tfidf, _docs, _name_index

    catalog_path = Path(CATALOG_PATH)
    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Catalog not found at {catalog_path}. "
            "Run the scraper first: python download_catalog.py"
        )

    with open(catalog_path, "r", encoding="utf-8") as f:
        _catalog = json.load(f)
    print(f"[catalog] Loaded {len(_catalog)} assessments.")

    _name_index = {item["name"].lower().strip(): i for i, item in enumerate(_catalog)}
    _docs = [_make_doc(item) for item in _catalog]

    tokenized = [_tokenize(d) for d in _docs]
    _bm25 = BM25Okapi(tokenized)

    _tfidf = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=30000)
    _tfidf_matrix = _tfidf.fit_transform(_docs)
    print("[catalog] BM25 + TF-IDF indexes built.")


def get_all() -> list[dict]:
    return list(_catalog)


def get_by_name(name: str) -> dict | None:
    key = name.lower().strip()
    if key in _name_index:
        return dict(_catalog[_name_index[key]])
    for item in _catalog:
        if key in item["name"].lower():
            return dict(item)
    return None


def get_by_url(url: str) -> dict | None:
    return next((dict(i) for i in _catalog if i.get("url") == url), None)
