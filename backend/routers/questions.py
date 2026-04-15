from fastapi import APIRouter
from models import QuestionGenerateRequest
from services.question_gen import generate_questions
from config import HOTEL_NAMES

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/generate")
async def generate(req: QuestionGenerateRequest):
    """Generate 1-2 personalized follow-up questions based on review + hotel gaps."""
    hotel_name = HOTEL_NAMES.get(req.property_id, "this hotel")

    questions = await generate_questions(
        property_id=req.property_id,
        hotel_name=hotel_name,
        review_text=req.review_text,
        covered_dimensions=req.covered_dimensions,
    )

    return {
        "property_id": req.property_id,
        "questions": questions,
    }
