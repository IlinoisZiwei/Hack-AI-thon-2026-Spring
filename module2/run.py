"""
Module 2 — Intelligent Question Generation System
===================================================

Generates targeted survey questions for hotels based on Module 1 gap analysis.

Usage:
    python -m module2.run <module1_output.json>             # Process Module 1 JSON output
    python -m module2.run --demo                            # Use built-in demo data
    python -m module2.run --template-only                   # Template only, no LLM calls
    python -m module2.run --batch <multiple_hotels.json>    # Batch process multiple hotels

Output:
    hotel_questions_<property_id>.json  — Questions generated for a specific hotel
    or batch_questions_output.json       — Batch processing results
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import project config
try:
    sys.path.append(str(Path(__file__).parent.parent))
    from config import OPENAI_API_KEY
except ImportError:
    logger.warning("⚠️ Could not import config.py, will try environment variable for API key")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from .question_generator import generate_hotel_questions, process_multiple_hotels


def load_module1_output(file_path: str) -> Dict:
    """Load Module 1 JSON output."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"✅ Successfully loaded Module 1 output: {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        sys.exit(1)


def get_demo_data() -> Dict:
    """Return demo Module 1 output data."""
    return {
        "property_id": "demo_hotel_001",
        "top_gaps": [
            {
                "dimension": "breakfast_hours",
                "label": "Breakfast Hours",
                "category": "policy",
                "reason": "never_mentioned",
                "reason_label": "No data yet",
                "priority": 3,
                "mention_count": 0,
                "last_mentioned": None,
                "dominant_stance": None,
                "official_info": None
            },
            {
                "dimension": "wifi_speed",
                "label": "WiFi & Internet",
                "category": "hardware",
                "reason": "stale",
                "reason_label": "Last mentioned 8 months ago",
                "priority": 2,
                "mention_count": 12,
                "last_mentioned": "2025-08-15",
                "dominant_stance": "negative",
                "official_info": "Free WiFi in all rooms and public areas"
            },
            {
                "dimension": "room_cleanliness",
                "label": "Room Cleanliness",
                "category": "service",
                "reason": "official_conflict",
                "reason_label": "Official info conflicts with reviews (15 negative)",
                "priority": 4,
                "mention_count": 28,
                "last_mentioned": "2026-03-10",
                "dominant_stance": "negative",
                "official_info": "Daily housekeeping with premium cleaning standards"
            },
            {
                "dimension": "staff_friendliness",
                "label": "Staff & Service",
                "category": "service",
                "reason": "conflicting",
                "reason_label": "Mixed reviews — 8 positive / 6 negative",
                "priority": 1,
                "mention_count": 14,
                "last_mentioned": "2026-04-01",
                "dominant_stance": "mixed",
                "official_info": None
            },
            {
                "dimension": "parking",
                "label": "Parking",
                "category": "policy",
                "reason": "stale",
                "reason_label": "Last mentioned 6 months ago",
                "priority": 2,
                "mention_count": 5,
                "last_mentioned": "2025-10-15",
                "dominant_stance": "neutral",
                "official_info": "Self-parking available for $15/night"
            }
        ]
    }


def save_results(results: Dict, output_path: str):
    """Save results to a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Results saved to: {output_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")


def display_results(results: Dict):
    """Display results in a formatted terminal output."""
    print("\n" + "="*80)
    print("🏨 HOTEL QUESTION GENERATION RESULTS")
    print("="*80)

    property_id = results.get("property_id", "Unknown")
    print(f"🏨 Hotel: {property_id}")
    print(f"📝 Questions Generated: {results.get('questions_generated', 0)}")
    print(f"🛠️  Generation Method: {results.get('generation_method', 'unknown')}")
    print(f"📊 Input Gaps: {results.get('input_gaps_count', 0)}")

    print("\n" + "─"*80)
    print("GENERATED QUESTIONS:")
    print("─"*80)

    questions = results.get("questions", [])
    if not questions:
        print("❌ No questions generated")
        return

    for i, q in enumerate(questions, 1):
        question_text = q.get("question", "")
        gap_dim = q.get("gap_dimension", "")
        priority = q.get("priority", 0)
        source = q.get("source", "unknown")

        # Priority icons
        priority_icon = {4: "🚨", 3: "⚠️", 2: "📋", 1: "📝"}.get(priority, "❓")

        print(f"\n{i:2d}. {priority_icon} [{gap_dim}]")
        print(f"    {question_text}")
        print(f"    Source: {source} | Priority: {priority}")

        if q.get("expected_outcome"):
            print(f"    Expected: {q['expected_outcome']}")

    print("\n" + "="*80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Module 2: Intelligent Question Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m module2.run hotel_gaps.json           # Process a single hotel
  python -m module2.run --demo                    # Run demo
  python -m module2.run --template-only input.json  # Template only
  python -m module2.run --batch hotels.json       # Batch process
        """
    )

    parser.add_argument("input_file", nargs="?",
                      help="Path to Module 1 JSON output file")
    parser.add_argument("--demo", action="store_true",
                      help="Run demo with built-in sample data")
    parser.add_argument("--template-only", action="store_true",
                      help="Generate questions using templates only, no LLM calls")
    parser.add_argument("--batch", action="store_true",
                      help="Batch process multiple hotels (input file should contain an array)")
    parser.add_argument("--output", "-o",
                      help="Output file path (optional)")
    parser.add_argument("--max-questions", type=int, default=5,
                      help="Max questions per hotel (default: 5)")
    parser.add_argument("--no-display", action="store_true",
                      help="Don't display results in terminal")

    args = parser.parse_args()

    # Validate input
    if not args.demo and not args.input_file:
        parser.error("Must provide an input file or use --demo")

    # Get API key
    api_key = OPENAI_API_KEY
    if not api_key or api_key.startswith("your_"):
        logger.warning("⚠️ No valid OPENAI_API_KEY configured, will use template mode")
        api_key = None

    use_llm = not args.template_only and api_key is not None

    try:
        if args.demo:
            # Demo mode
            logger.info("🎯 Running demo mode")
            module1_data = get_demo_data()

            results = generate_hotel_questions(
                module1_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            output_path = args.output or "demo_questions.json"

        elif args.batch:
            # Batch processing mode
            logger.info("📦 Running batch processing mode")
            hotels_data = load_module1_output(args.input_file)

            if not isinstance(hotels_data, list):
                logger.error("❌ Batch mode requires input file to contain an array of hotels")
                sys.exit(1)

            results = process_multiple_hotels(
                hotels_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            output_path = args.output or "batch_questions_output.json"

            # Special display for batch results
            if not args.no_display:
                print(f"\n🏨 Batch processing complete: {len(results)} hotels")
                success_count = sum(1 for r in results if r.get('success', True))
                print(f"✅ Succeeded: {success_count} | ❌ Failed: {len(results) - success_count}")

        else:
            # Single hotel processing mode
            logger.info("🏨 Running single hotel processing mode")
            module1_data = load_module1_output(args.input_file)

            results = generate_hotel_questions(
                module1_data,
                openai_api_key=api_key,
                use_llm=use_llm,
                max_questions=args.max_questions
            )

            property_id = results.get("property_id", "unknown")[:12]
            output_path = args.output or f"hotel_questions_{property_id}.json"

        # Save results
        save_results(results, output_path)

        # Display results (unless batch mode or user disabled)
        if not args.no_display and not args.batch:
            display_results(results)

        logger.info("🎉 Module 2 complete!")

    except KeyboardInterrupt:
        logger.info("⏹️  Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Run failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()