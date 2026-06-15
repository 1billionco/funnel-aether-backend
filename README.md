# Funnel Aether Backend

**AI-Powered All-in-One Marketing Operating System for SMEs**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange.svg)](https://python.langchain.com/)

This is the official **Python backend** for **Funnel Aether** — a human-AI hybrid marketing platform that replaces fragmented tools with one intelligent system for the entire customer acquisition funnel.

## Vision

Funnel Aether gives resource-constrained SMEs and small marketing teams (1–5 people) a single, clean platform to manage **content, campaigns, leads, and analytics** — with AI doing the heavy lifting while humans retain full creative and strategic control.

**Core Philosophy**
- AI handles generation, optimization, and insights at scale.
- Humans stay in full control (brand voice training, review, strategy, final approval).
- Brand voice is the single source of truth.
- Every AI output is editable by default.
- Clean, modern SaaS experience (inspired by Canva + Notion + Linear).

Initial focus markets: **UK + Nigeria**.

## Current Status

**✅ Brand Voice Training module is complete** (foundational RAG system)

We are building the platform iteratively, one high-quality module at a time.

### MVP Roadmap

| Priority | Module                        | Status     | Description |
|----------|-------------------------------|------------|-------------|
| 1        | Brand Voice Training          | ✅ Done    | RAG-powered voice learning & context retrieval |
| 2        | Content Studio                | ⏳ Next    | On-brand content generation (social, email, ads, landing pages) |
| 3        | Dashboard + AI Co-Pilot       | ⏳ Pending | Overview + contextual AI assistant |
| 4        | Audience & Leads              | ⏳ Pending | Basic CRM + AI lead scoring |
| 5        | Campaigns & Automation        | ⏳ Pending | Visual builder + email automation |
| 6        | Analytics                     | ⏳ Pending | Funnel visualization + ROI reporting |

## Tech Stack

**Backend**
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic
- Pydantic v2

**AI Layer**
- LangChain + Chroma (vector store for RAG)
- Pluggable LLM providers (Anthropic Claude, OpenAI, Grok)

**Database**
- SQLite (development)
- PostgreSQL (production)

## Project Structure

```
funnel_aether_backend/
├── app/
│   ├── main.py                 # FastAPI application entrypoint
│   ├── core/
│   │   └── config.py           # Settings & environment configuration
│   ├── api/v1/endpoints/       # API route handlers
│   ├── models/                 # SQLAlchemy database models
│   ├── schemas/                # Pydantic request/response models
│   ├── services/
│   │   ├── brand_voice/        # RAG brand voice training & retrieval
│   │   ├── ai/                 # LLM orchestration layer
│   │   ├── campaigns/          # (future)
│   │   └── analytics/          # (future)
│   └── db/                     # Database session & base
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Getting Started (Development)

```bash
# Clone the repository
git clone https://github.com/adoghe_joshua/funnel-aether-backend.git
cd funnel-aether-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive API documentation (Swagger UI).

## Environment Variables

Copy `.env.example` to `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
# or GROK_API_KEY
```

## Key Features (Current)

- **Brand Voice Training** via document upload (RAG)
- Semantic retrieval of brand context before any generation
- Clean separation of concerns (services, schemas, models)
- Human-in-the-loop design from day one
- Ready for easy extension to Content Studio and beyond

## Next Steps

We are ready to build the **Content Studio** module next — the AI-powered content generator that consumes the brand voice context we just built.

Would you like to continue with:
- Content Studio (recommended)
- AI Co-Pilot
- Or improve the current Brand Voice module?

---

**Built collaboratively with Grok** as part of the Funnel Aether Master's research project.
