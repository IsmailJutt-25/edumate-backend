"""
EduMate AI - FastAPI Backend
AI-powered study material generation service
"""

import os
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="EduMate AI API",
    description="AI-powered study material generation API",
    version="1.0.0"
)

# Configure CORS
# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://ffed5wkusnwpe.ok.kimi.link,http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic Models
class MCQ(BaseModel):
    question: str
    options: List[str]
    answer: str

class Flashcard(BaseModel):
    front: str
    back: str

class StudyData(BaseModel):
    notes: List[str]
    mcqs: List[MCQ]
    flashcards: List[Flashcard]

class GenerationRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200, description="The study topic to generate materials for")

class GenerationResponse(BaseModel):
    success: bool
    data: Optional[StudyData] = None
    error: Optional[str] = None

# AI Prompt Template
STUDY_GENERATION_PROMPT = """You are EduMate AI, an expert educational content creator. Your task is to generate comprehensive study materials for the given topic.

TOPIC: {topic}

Generate study materials in the following STRICT JSON format:

{{
  "notes": [
    "Clear, concise bullet point summarizing a key concept",
    "Another important point about the topic",
    "Continue with 5-7 bullet points total"
  ],
  "mcqs": [
    {{
      "question": "What is the main concept of...?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "answer": "A"
    }}
  ],
  "flashcards": [
    {{
      "front": "Key term or question",
      "back": "Clear explanation or definition"
    }}
  ]
}}

REQUIREMENTS:
1. NOTES: Generate 5-7 bullet points that clearly explain the topic. Use simple, student-friendly language.
2. MCQs: Generate EXACTLY 5 multiple-choice questions. Each must have 4 options (A, B, C, D) with one correct answer.
3. FLASHCARDS: Generate EXACTLY 3 flashcards with question/term on front and explanation on back.
4. All content must be accurate, educational, and appropriate for high school or early college level.
5. Return ONLY valid JSON. No markdown formatting, no code blocks, no additional text.

Ensure the JSON is properly formatted with double quotes and valid syntax."""


def clean_json_response(response_text: str) -> str:
    """Clean the AI response to extract valid JSON."""
    # Remove markdown code blocks if present
    response_text = re.sub(r'```json\s*', '', response_text)
    response_text = re.sub(r'```\s*', '', response_text)
    
    # Strip whitespace
    response_text = response_text.strip()
    
    return response_text


def validate_study_data(data: dict) -> StudyData:
    """Validate and clean the generated study data."""
    # Ensure notes is a list of strings
    notes = data.get("notes", [])
    if not isinstance(notes, list):
        notes = [str(notes)]
    notes = [str(note) for note in notes if note]
    
    # Ensure mcqs is a list with exactly 5 items
    mcqs = data.get("mcqs", [])
    if not isinstance(mcqs, list):
        mcqs = []
    
    validated_mcqs = []
    for mcq in mcqs[:5]:  # Take only first 5
        if isinstance(mcq, dict):
            options = mcq.get("options", [])
            if len(options) != 4:
                # Fix options if not exactly 4
                while len(options) < 4:
                    options.append(f"{chr(65 + len(options))}) Option {len(options) + 1}")
                options = options[:4]
            
            validated_mcqs.append({
                "question": str(mcq.get("question", "Question")),
                "options": [str(opt) for opt in options],
                "answer": str(mcq.get("answer", "A")).upper()
            })
    
    # Ensure flashcards is a list with exactly 3 items
    flashcards = data.get("flashcards", [])
    if not isinstance(flashcards, list):
        flashcards = []
    
    validated_flashcards = []
    for card in flashcards[:3]:  # Take only first 3
        if isinstance(card, dict):
            validated_flashcards.append({
                "front": str(card.get("front", "Question")),
                "back": str(card.get("back", "Answer"))
            })
    
    return StudyData(
        notes=notes,
        mcqs=validated_mcqs,
        flashcards=validated_flashcards
    )


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "EduMate AI API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "edumate-ai"}


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_study_material(request: GenerationRequest):
    """
    Generate study materials (notes, MCQs, flashcards) for a given topic.
    
    Args:
        request: GenerationRequest containing the topic
        
    Returns:
        GenerationResponse with success status and study data
    """
    try:
        # Validate topic
        topic = request.topic.strip()
        if not topic:
            return GenerationResponse(
                success=False,
                error="Topic cannot be empty"
            )
        
        # Prepare the prompt
        prompt = STUDY_GENERATION_PROMPT.format(topic=topic)
        
       # Call OpenAI API
response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
        {
            "role": "system",
            "content": "You are an expert educational content creator. Always respond with valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.7,
    max_tokens=2000
)

response_text = response.choices[0].message.content
cleaned_response = clean_json_response(response_text)
        
        try:
            parsed_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            return GenerationResponse(
                success=False,
                error=f"Failed to parse AI response: {str(e)}"
            )
        
        # Validate and structure the data
        study_data = validate_study_data(parsed_data)
        
        return GenerationResponse(
            success=True,
            data=study_data
        )
        
    except Exception as e:
        error_message = str(e)
        if "api_key" in error_message.lower():
            error_message = "API configuration error. Please contact support."
        elif "rate limit" in error_message.lower():
            error_message = "Too many requests. Please try again in a moment."
        
        return GenerationResponse(
            success=False,
            error=error_message
        )


# For local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
