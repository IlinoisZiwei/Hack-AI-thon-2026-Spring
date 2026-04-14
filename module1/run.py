"""
Module 1 — Hotel Information Profile Construction Pipeline

Usage:
    python -m module1.run                          # rule-based, all reviews
    python -m module1.run --use-llm                # LLM extraction (gpt-4o-mini)
    python -m module1.run --sample 200             # quick test with 200 reviews
    python -m module1.run --output my_output.json  # custom output path
    python -m module1.run --hotel <property_id>    # single hotel deep-dive

Output:
    output/hotel_profiles.json  — full profiles + gaps for every hotel
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # reads .env from CWD or any parent

from .description_enricher import build_official_info
from .dimensions import DIMENSION_RATING_MAP, DIMENSIONS
from .extractor import extract_llm_batch, extract_rule_based
from .gap_finder import find_gaps
from .profiler import build_hotel_profiles, compute_completeness, merge_official_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Auto-detect data directory relative to this file
_HERE = Path(__file__).resolve().parent
DATA_DIR_DEFAULT = _HERE.parent / "WAIAI Hack-AI-thon Resources" / "data"


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    reviews = pd.read_csv(data_dir / "Reviews_PROC.csv")
    descriptions = pd.read_csv(data_dir / "Description_PROC.csv")
    logger.info("Loaded %d reviews, %d property descriptions", len(reviews), len(descriptions))
    return reviews, descriptions


def preprocess_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    reviews = reviews[
        ["eg_property_id", "acquisition_date", "lob", "rating", "review_title", "review_text"]
    ].copy()

    reviews["acquisition_date"] = pd.to_datetime(reviews["acquisition_date"], errors="coerce")

    def _parse_rating(x):
        if pd.isna(x):
            return {}
        try:
            return json.loads(x)
        except Exception:
            return {}

    reviews["rating_dict"] = reviews["rating"].apply(_parse_rating)
    reviews["overall_rating"] = reviews["rating_dict"].apply(lambda d: d.get("overall"))
    reviews["review_title"] = reviews["review_title"].fillna("").astype(str)
    reviews["review_text"] = reviews["review_text"].fillna("").astype(str)

    def _combine(title: str, text: str) -> str:
        title, text = title.strip(), text.strip()
        if title and text:
            return f"{title}. {text}"
        return title or text

    reviews["review_full_text"] = reviews.apply(
        lambda row: _combine(row["review_title"], row["review_text"]), axis=1
    )

    def _clean(text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s.,!?'-]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    reviews["review_text_clean"] = reviews["review_full_text"].apply(_clean)
    reviews = reviews[reviews["review_text_clean"].str.len() > 0].copy()
    logger.info("%d reviews remain after cleaning", len(reviews))
    return reviews


# ── Extraction ────────────────────────────────────────────────────────────────

def run_extraction(rows: list[dict], use_llm: bool) -> list[dict]:
    """Run extraction and flatten results into a list of dimension records."""
    dimension_records: list[dict] = []

    if use_llm:
        logger.info("Extracting with LLM (gpt-4o-mini), batch_size=10 …")
        batch_mentions = extract_llm_batch(rows, model="gpt-4o-mini", batch_size=10)
        for row, mentions in zip(rows, batch_mentions):
            for m in mentions:
                dimension_records.append({
                    "eg_property_id": row["eg_property_id"],
                    "dimension": m["dimension"],
                    "category": DIMENSIONS[m["dimension"]]["category"],
                    "stance": m["stance"],
                    "confidence": m["confidence"],
                    "source": m["source"],
                    "review_date": row["acquisition_date"],
                    "evidence": m.get("evidence", ""),
                })
    else:
        logger.info("Extracting with rule-based method …")
        for row in rows:
            for m in extract_rule_based(row):
                dimension_records.append({
                    "eg_property_id": row["eg_property_id"],
                    "dimension": m["dimension"],
                    "category": DIMENSIONS[m["dimension"]]["category"],
                    "stance": m["stance"],
                    "confidence": m["confidence"],
                    "source": m["source"],
                    "review_date": row["acquisition_date"],
                    "evidence": m["evidence"],
                })

    logger.info("Extracted %d dimension mentions total", len(dimension_records))
    return dimension_records


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Module 1: Hotel Profile Builder")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR_DEFAULT,
                        help="Path to data directory")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only N reviews (for quick testing)")
    parser.add_argument("--use-llm", action="store_true",
                        help="Use GPT-4o-mini for extraction (requires OPENAI_API_KEY)")
    parser.add_argument("--output", type=Path, default=Path("output/hotel_profiles.json"),
                        help="Output JSON path")
    parser.add_argument("--hotel", type=str, default=None,
                        help="Print detailed profile for a specific property_id prefix")
    args = parser.parse_args()

    # ── Load & preprocess ────────────────────────────────────────────
    reviews_raw, descriptions = load_data(args.data_dir)
    reviews = preprocess_reviews(reviews_raw)

    if args.sample:
        reviews = reviews.sample(n=min(args.sample, len(reviews)), random_state=42)
        logger.info("Sampled %d reviews", len(reviews))

    # ── Extract dimensions ───────────────────────────────────────────
    rows = reviews.to_dict("records")
    dimension_records = run_extraction(rows, use_llm=args.use_llm)

    dimension_mentions = pd.DataFrame(dimension_records)

    # ── Build profiles ───────────────────────────────────────────────
    all_property_ids = sorted(reviews["eg_property_id"].dropna().unique().tolist())
    logger.info("Building profiles for %d hotels …", len(all_property_ids))

    hotel_profiles = build_hotel_profiles(dimension_mentions, all_property_ids)

    # ── Enrich with official Description data ────────────────────────
    logger.info("Enriching profiles with Description_PROC data …")
    official_info = build_official_info(descriptions)
    hotel_profiles = merge_official_info(hotel_profiles, official_info)

    # ── Gap analysis ─────────────────────────────────────────────────
    current_date = datetime.now()
    output: dict = {}

    for pid, profile in hotel_profiles.items():
        completeness = compute_completeness(profile)
        gaps = find_gaps(profile, current_date)
        output[pid] = {
            "profile": profile,
            "completeness": completeness,
            "gaps": gaps,
            "top_gaps": gaps[:5],  # top 5 for quick access
        }

    # ── Save ─────────────────────────────────────────────────────────
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info("Saved → %s", args.output)

    # ── Summary table ────────────────────────────────────────────────
    print("\n" + "═" * 64)
    print("  HOTEL PROFILE SUMMARY")
    print("═" * 64)
    print(f"  {'Hotel ID':20s}  {'Complete':>8}  {'Gaps':>5}  Top gap")
    print("─" * 64)
    for pid, data in output.items():
        c = data["completeness"]
        g = data["gaps"]
        top = g[0] if g else None
        top_str = f"[{top['reason']}] {top['label']}" if top else "—"
        print(f"  {pid[:18]+'..':<20}  {c['completeness_score']:>7.1f}%  {len(g):>5}  {top_str}")
    print("═" * 64)

    # ── Optional single-hotel deep-dive ─────────────────────────────
    if args.hotel:
        matches = [pid for pid in output if pid.startswith(args.hotel)]
        if not matches:
            print(f"\nNo hotel found with ID prefix '{args.hotel}'")
        else:
            pid = matches[0]
            data = output[pid]
            print(f"\n── Profile: {pid[:32]}… ──────────────────")
            print(f"  Completeness: {data['completeness']['completeness_score']}%")
            print(f"\n  Top gaps:")
            for g in data["top_gaps"]:
                print(f"    [{g['priority']}] {g['label']:<30} {g['reason_label']}")
            print(f"\n  Dimension detail:")
            for dim, info in data["profile"].items():
                bar = "█" * min(info["mention_count"], 20)
                print(f"    {dim:<28} {info['mention_count']:>4}  {bar}  "
                      f"{info['dominant_stance'] or '—'}")


if __name__ == "__main__":
    main()
