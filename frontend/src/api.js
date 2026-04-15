const BASE = '/api';

export async function fetchHotels() {
  const res = await fetch(`${BASE}/hotels`);
  return res.json();
}

export async function fetchHotelProfile(propertyId) {
  const res = await fetch(`${BASE}/hotels/${propertyId}/profile`);
  return res.json();
}

export async function analyzeReview(propertyId, reviewText) {
  const res = await fetch(`${BASE}/reviews/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ property_id: propertyId, review_text: reviewText }),
  });
  return res.json();
}

export async function generateQuestions(propertyId, reviewText, coveredDimensions) {
  const res = await fetch(`${BASE}/questions/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      property_id: propertyId,
      review_text: reviewText,
      covered_dimensions: coveredDimensions,
    }),
  });
  return res.json();
}

export async function submitAnswer(propertyId, dimension, answer, sentiment) {
  const res = await fetch(`${BASE}/reviews/submit-answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      property_id: propertyId,
      dimension,
      answer,
      sentiment,
    }),
  });
  return res.json();
}
