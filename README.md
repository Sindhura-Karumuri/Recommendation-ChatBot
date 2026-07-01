# SHL Assessment Recommender

Conversational agent that helps hiring managers select SHL Individual Test Solution assessments through natural dialogue.

## Project Structure

```
SHL/
├── backend/
│   ├── api/
│   │   └── routes.py          # FastAPI route handlers
│   ├── services/
│   │   ├── agent.py           # Conversational agent logic
│   │   ├── catalog.py         # Catalog loading & indexing
│   │   ├── retrieval.py       # BM25 + TF-IDF hybrid search
│   │   └── comparator.py      # Assessment comparison helper
│   ├── models/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── prompts.py             # System prompt & refusal patterns
│   ├── config.py              # Environment config
│   └── main.py                # FastAPI app entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/        # ChatMessage, RecommendationCard, TypingIndicator
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── data/
│   └── shl_catalog.json       # 377 SHL Individual Test Solutions
├── tests/
│   ├── test_health.py
│   └── test_chat.py
├── docs/
├── .env.example
├── Dockerfile
├── render.yaml
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # add your GROQ_API_KEY
```

Get a free Groq key at https://console.groq.com

## Run

Backend:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

## API

`GET /health` → `{"status": "ok"}`

`POST /chat`
```json
{
  "messages": [
    {"role": "user", "content": "Hiring a mid-level Java developer"}
  ]
}
```
Response:
```json
{
  "reply": "...",
  "recommendations": [
    {"name": "Java 8 (New)", "url": "https://www.shl.com/...", "test_type": "K"}
  ],
  "end_of_conversation": false
}
```

## Tests

```bash
python tests/test_health.py
python tests/test_chat.py
```

## Docker

```bash
docker build -t shl-recommender .
docker run -e GROQ_API_KEY=your_key -p 8000:7860 shl-recommender
```
