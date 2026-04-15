# 🏨 Hotel Review Analysis & Intelligent Question Generation System

**Hack-AI-thon 2026 Spring Project**

An end-to-end hotel information analysis system that automatically identifies service gaps by analyzing customer review data and generates personalized guest survey questions for each hotel. The system combines machine learning, natural language processing, and LLM-enhanced techniques to provide data-driven solutions for hotel operations optimization.

---

## 🎯 System Overview

### 🔄 Workflow
```
Customer Review Data → Module 1 (Gap Analysis) → Module 2 (Question Generation) → Guest Survey Questions
```

### 📦 Module Architecture

**Module 1: Hotel Information Profile Builder**
- 🔍 Extracts 20 hotel service dimensions from customer reviews
- 📊 Builds a service quality profile for each hotel
- 🚨 Identifies and scores service gaps (4 types)
- 📈 Prioritizes based on business importance

**Module 2: Intelligent Question Generator**
- 🤖 Generates personalized questions based on gap analysis results
- 💬 Uses OpenAI LLM to enhance question naturalness
- 📋 Template fallback mechanism ensures system stability
- 🎯 Generates simple, easy-to-answer guest survey questions

---

## 🚀 Quick Start

### 1️⃣ Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure API Key

Edit `config.py`:
```python
OPENAI_API_KEY = "your_openai_api_key_here"
```

### 3️⃣ Run the System

**Module 1 — Gap Analysis:**
```bash
# Use sample data
python -m module1.run --sample

# Analyze a specific hotel
python -m module1.run --hotel hotel_id_123

# Batch analysis
python -m module1.run Reviews_PROC.csv --output results/
```

**Module 2 — Question Generation:**
```bash
# Demo mode (recommended)
python -m module2.run --demo

# Process Module 1 output
python -m module2.run hotel_gaps.json

# Template only (no API calls)
python -m module2.run --template-only input.json

# Batch process multiple hotels
python -m module2.run --batch hotels_list.json
```

---

## 📊 Core Features

### 🔍 Module 1: Gap Identification System

**20 Hotel Service Dimensions:**
- **Hardware & Facilities** (7 dimensions): WiFi, air conditioning, TV, parking, etc.
- **Service Experience** (8 dimensions): Staff attitude, room cleanliness, breakfast, etc.
- **Surroundings** (3 dimensions): Location, noise, nearby amenities
- **Hotel Policies** (2 dimensions): Check-in/out, pet policy

**4 Gap Types:**
1. 🔴 **Official Conflict** (Priority 4) — Official info contradicts guest reviews
2. 🟡 **Never Mentioned** (Priority 3) — Lacking guest feedback data
3. 🟠 **Stale Info** (Priority 2) — Feedback too old, needs refresh
4. 🟢 **Conflicting Reviews** (Priority 1) — Inconsistent guest opinions

### 🤖 Module 2: Intelligent Question Generation

**Question Generation Strategy:**
- **LLM-Enhanced Mode**: Uses GPT-3.5-turbo for natural conversational questions
- **Template Fallback Mode**: Rule-based structured question generation
- **Personalized Design**: Each hotel receives 5 unique questions

**Question Examples:**
```
City Business Hotel:
- "How was the WiFi speed and connection stability?"
- "What did you think about the room cleanliness?"

Beachfront Resort:
- "When did you last use the hotel pool?"
- "Have you visited the hotel's beach recently?"
```

---

## 📁 Project Structure

```
Hack-AI-thon-2026-Spring/
├── 📂 module1/                 # Gap Analysis Module
│   ├── dimensions.py          # 20 hotel dimension definitions
│   ├── extractor.py           # Keyword extractor
│   ├── profiler.py            # Hotel profile builder
│   ├── gap_finder.py          # Gap identification & scoring
│   ├── business_weights.py    # Business importance weights
│   └── run.py                 # CLI entry point
├── 📂 module2/                 # Question Generation Module
│   ├── question_templates.py  # Question template system
│   ├── question_generator.py  # LLM-enhanced generator
│   └── run.py                 # CLI entry point
├── 📊 Reviews_PROC.csv        # Customer review data
├── ⚙️ config.py               # API configuration
├── 📋 requirements.txt        # Dependencies
└── 📖 README.md              # Project documentation
```

---

## 🛠️ Detailed Usage

### Module 1 Advanced Options

```bash
# Specify output format and location
python -m module1.run --sample --format json --output results/

# Enable LLM-enhanced extraction (experimental)
python -m module1.run --sample --use-llm

# Adjust scoring threshold
python -m module1.run --sample --min-gap-score 30.0

# Verbose debug information
python -m module1.run --sample --verbose
```

### Module 2 Advanced Options

```bash
# Control number of generated questions
python -m module2.run --demo --max-questions 3

# Specify output file
python -m module2.run input.json --output custom_questions.json

# Suppress terminal output
python -m module2.run --batch hotels.json --no-display
```

---

## 📈 Output Format

### Module 1 Output (JSON):
```json
{
  "property_id": "hotel_001",
  "top_gaps": [
    {
      "dimension": "wifi_speed",
      "label": "WiFi & Internet",
      "category": "hardware",
      "reason": "stale",
      "priority": 2,
      "mention_count": 12,
      "last_mentioned": "2025-08-15",
      "dominant_stance": "negative"
    }
  ]
}
```

### Module 2 Output (JSON):
```json
{
  "property_id": "hotel_001",
  "questions_generated": 5,
  "generation_method": "llm_enhanced",
  "questions": [
    {
      "question": "How was the WiFi speed and connection stability?",
      "gap_dimension": "wifi_speed",
      "gap_reason": "stale",
      "priority": 2,
      "expected_outcome": "Understand guest perception of WiFi quality"
    }
  ]
}
```

---

## ⚙️ Configuration

### API Usage Control
- **Cost Control**: Uses GPT-3.5-turbo to minimize API costs
- **Template Fallback**: Automatically uses templates when API calls fail
- **Batch Optimization**: Supports batch processing to reduce API call count

### Scoring System Tuning
Edit `module1/business_weights.py` to adjust dimension weights:
```python
BUSINESS_WEIGHTS = {
    "wifi_speed": 4.5,      # High priority
    "room_cleanliness": 4.8, # Highest priority
    "parking": 2.1,          # Lower priority
}
```

---

## 🤝 Contributing

1. Fork the project
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push the branch: `git push origin feature/amazing-feature`
5. Submit a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🏆 Hack-AI-thon 2026 Spring

This project is a Hack-AI-thon 2026 Spring competition entry, focused on applying AI technology to data-driven decision optimization in the hotel industry.

**Core Innovations:**
- 🎯 End-to-end hotel information gap identification and question generation pipeline
- 🤖 LLM-enhanced natural language question generation
- 📊 Intelligent prioritization based on business importance
- 🔄 Template fallback mechanism for system stability

---

**Project Link**: https://github.com/dengjiaming/Hack-AI-thon-2026-Spring