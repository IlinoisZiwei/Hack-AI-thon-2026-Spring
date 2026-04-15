from fastapi import APIRouter
from models import ReviewRequest, ReviewAnalysis, AnswerSubmission
from services.review_parser import extract_dimensions
from services.gap_analyzer import update_dimension, get_hotel_profile, compute_completeness
from config import HOTEL_NAMES

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/analyze")
async def analyze_review(req: ReviewRequest):
    """Analyze a review and extract covered dimensions."""
    covered = await extract_dimensions(req.review_text)
    return ReviewAnalysis(
        property_id=req.property_id,
        review_text=req.review_text,
        covered_dimensions=covered,
    )


@router.post("/submit-answer")
async def submit_answer(answer: AnswerSubmission):
    """Submit user's answer to a follow-up question and update hotel profile."""
    update_dimension(
        property_id=answer.property_id,
        dimension=answer.dimension,
        answer=answer.answer,
        sentiment=answer.sentiment,
    )

    profile = get_hotel_profile(answer.property_id)
    completeness = None
    if profile:
        completeness = compute_completeness(profile.get("profile", profile))

    return {
        "status": "success",
        "property_id": answer.property_id,
        "dimension_updated": answer.dimension,
        "new_completeness": completeness,
    }
