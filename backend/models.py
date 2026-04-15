from pydantic import BaseModel


class ReviewRequest(BaseModel):
    property_id: str
    review_text: str


class ReviewAnalysis(BaseModel):
    property_id: str
    review_text: str
    covered_dimensions: list[str]


class QuestionGenerateRequest(BaseModel):
    property_id: str
    review_text: str
    covered_dimensions: list[str]


class GeneratedQuestion(BaseModel):
    question: str
    gap_dimension: str
    gap_label: str
    gap_reason: str
    priority: int


class QuestionGenerateResponse(BaseModel):
    property_id: str
    questions: list[GeneratedQuestion]


class AnswerSubmission(BaseModel):
    property_id: str
    dimension: str
    answer: str
    sentiment: str  # "positive", "negative", "neutral"
