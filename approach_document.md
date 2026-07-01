# SHL Assessment Recommender — Approach Document

## Problem & Design Goals

The task is a conversational agent that takes a hiring manager from a vague role description to a grounded shortlist of SHL Individual Test Solution assessments. The core challenges are: (1) retrieval quality — finding the right assessments from 377 items given noisy natural-language queries, (2) conversational behavior — knowing when to clarify vs. recommend vs. compare, and (3) strict schema compliance and scope control for automated evaluation.

---

## Retrieval Setup

I chose a **hybrid BM25 + TF-IDF retrieval** with **Reciprocal Rank Fusion (RRF)**, without any external vector database or embedding service. Each catalog item is indexed as a rich text document combining name, description, test type labels, job levels, languages, and duration.

**Why not embeddings?**  
The catalog is only 377 items. Dense embeddings add latency and a dependency (OpenAI/HuggingFace) for marginal gain at this scale. BM25 handles exact keyword matching well (e.g. "Java 8", "OPQ32r"), while TF-IDF bigrams capture multi-word phrases ("data science", "machine learning"). RRF merges both rank lists without needing to tune score normalization.

The retrieval query is built from the last 8 conversation turns concatenated, so refinements ("also add personality tests") naturally shift the retrieved context toward the new constraint.

---

## Agent / Prompt Design

The agent uses **Groq's `llama-3.3-70b-versatile`** (free tier, ~200 tok/s) for low-latency responses within the 30-second timeout.

**Prompt structure:**  
1. A strict system prompt with behavioral rules (clarify before recommending, 1–10 recs, refine not restart, refuse off-topic).  
2. A dynamic catalog context block injected per turn (top-20 retrieved items formatted with name, URL, type codes, levels, duration, description excerpt).  
3. Full conversation history (last 12 messages).  
4. A turn-awareness note injected at turn 5+ to push the agent toward committing to recommendations.

The model is instructed to return **JSON only** (`response_format: json_object`) which eliminates parsing fragility from markdown fences.

**Scope control:**  
Off-topic requests (prompt injection, salary, legal, competitors) are caught by a pre-LLM regex guard before any API call, ensuring zero hallucination risk on those paths.

**Recommendation validation:**  
Every recommendation returned by the LLM is cross-checked against the catalog by name lookup. If the URL is missing or non-SHL, it is patched from the catalog or the item is dropped entirely. This ensures 100% of returned URLs are real catalog URLs.

---

## What Didn't Work

- **Static scraping** of the SHL catalog page failed — the site is JS-rendered. The raw catalog was sourced from the provided JSON endpoint directly, then normalized with `prepare_catalog.py`.
- **Sentence-transformers + FAISS** was initially in requirements but removed — the embedding model download (~400MB) made cold starts exceed the 2-minute limit on free hosting tiers. BM25+TF-IDF loads in ~0.3s.
- **High temperature (0.3+)** caused the model to occasionally invent assessment names. Dropping to 0.1 made outputs consistent and catalog-grounded.

---

## Evaluation Approach

**Automated probes (run via `test_behavior_probes.py`):**
- No recs on vague turn-1 query
- Off-topic refusal (prompt injection, salary)
- All URLs are valid SHL catalog URLs
- Schema compliance on every response
- Refinement updates the shortlist
- Recs capped at 10

**Multi-turn trace test (`test_conversation.py`):**  
Simulates a 5-turn conversation: vague query → clarify → refine with personality test → compare two assessments → add cognitive test → close. Validated that EOC fires, schema holds, and recs come from catalog.

**Recall@10:**  
The hybrid retrieval consistently surfaces the most relevant items (verified manually for Java, Python, sales, and data science roles). Turn-awareness injection ensures the agent commits to a shortlist before the 8-turn cap.

---

## Stack Summary

| Component | Choice | Reason |
|---|---|---|
| API framework | FastAPI | Fast, async, Pydantic validation |
| LLM | Groq / llama-3.3-70b | Free tier, <1s latency |
| Retrieval | BM25 + TF-IDF (rank-bm25, scikit-learn) | No external deps, fast cold start |
| Deployment | Render (render.yaml) | Free tier, auto-deploy from repo |
| AI tools used | Kiro (agentic coding assistant) | Scaffolding, file generation, iteration |
