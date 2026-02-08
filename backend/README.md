# EduMate AI Backend

FastAPI backend for EduMate AI - AI-powered study material generation.

## Features

- Generate structured study notes from any topic
- Create 5 MCQs with answers and explanations
- Generate 3 flashcards for quick review
- Clean, deterministic JSON output
- CORS enabled for frontend integration

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

3. Run the server:
```bash
python main.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### GET /
Health check and API info.

### POST /api/generate
Generate study materials for a topic.

**Request Body:**
```json
{
  "topic": "Photosynthesis"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "notes": ["...", "..."],
    "mcqs": [
      {
        "question": "...",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "answer": "A"
      }
    ],
    "flashcards": [
      {
        "front": "...",
        "back": "..."
      }
    ]
  }
}
```

## Deployment

### Render
1. Create a new Web Service
2. Connect your GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `OPENAI_API_KEY`

### Railway
1. Create a new project
2. Deploy from GitHub repo
3. Add environment variable: `OPENAI_API_KEY`
