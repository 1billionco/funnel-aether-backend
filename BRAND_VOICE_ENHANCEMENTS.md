# Brand Voice Module - Enhanced Features

## Overview
The Brand Voice module has been significantly enhanced to support the dissertation requirements for an AI-powered marketing platform serving global SMEs (UK, Nigeria, and beyond).

## Key Enhancements

### 1. Multi-Language Support 🌍
- **Primary Language**: Set brand's primary language (ISO code)
- **Supported Languages**: Define multiple languages for international brands
- **Language-Aware Retrieval**: RAG system prioritizes documents in the target language
- **Document Language Tracking**: Each document tracks its language for better filtering

**Use Case**: A Nigerian e-commerce brand can serve customers in English, Yoruba, and Hausa with appropriate brand voice for each language.

### 2. Quality Scoring System 📊
- **Training Quality Score (0-100)**: Automatically calculated based on:
  - Document type diversity (40 points)
  - Required document types present (20 points)
  - Content volume/chunks (30 points)
  - Document count (10 points)
- **Confidence Scoring**: Context retrieval confidence scales with quality score (0.6-0.95)

**Benefit**: Users know exactly how well-trained their brand voice is and what to improve.

### 3. Smart Recommendations 💡
- **Missing Document Types**: Suggests which document types to add next
- **Priority Ordering**: Prioritizes essential types (guidelines, tone_examples, past_content)
- **Actionable Insights**: Provides specific recommendations like:
  - "Define tone descriptors (e.g., 'professional, friendly, authoritative')"
  - "Upload more content to improve AI understanding"
  - "Specify your target audience for better targeting"

### 4. Enhanced Brand Profile Fields 🎯
New fields for precise brand voice control:
- `tone_descriptors`: Comma-separated adjectives (e.g., "professional, witty, empathetic")
- `writing_style`: Style classification (e.g., "conversational", "formal", "technical")
- `brand_personality`: Archetype description (e.g., "friendly expert", "bold innovator")

### 5. Document Management 📁
- **Soft Delete**: Documents can be deactivated without permanent deletion
- **Relevance Tracking**: Tracks how often each document is retrieved
- **Last Retrieved Timestamp**: Know which documents are most useful
- **Source Tracking**: Store original filenames and source URLs

### 6. Comprehensive Analysis API 🔍
New `/api/v1/brand-voice/analysis` endpoint provides:
- Overall training score
- Document diversity score
- Content coverage score
- Strengths identification
- Actionable recommendations
- Missing document types

## New API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/brand-voice/analysis` | Get comprehensive brand voice analysis |
| GET | `/api/v1/brand-voice/documents` | List all brand documents |
| DELETE | `/api/v1/brand-voice/documents/{id}` | Soft-delete a document |

## Enhanced Existing Endpoints

### POST `/api/v1/brand-voice/upload`
Now returns:
- `training_quality_score`: Quality score after upload
- Better multi-language support

### POST `/api/v1/brand-voice/context`
Now accepts:
- `language`: Optional target language for retrieval

Now returns:
- `primary_language`: Brand's primary language
- `recommended_document_types`: Suggestions for improvement
- `confidence`: Dynamic score based on training quality

## Database Schema Changes

### BrandProfile Model
```python
# New fields added:
tone_descriptors: Text
writing_style: String(50)
brand_personality: Text
primary_language: String(10)  # default "en"
supported_languages: Text  # JSON array
total_chunks: Integer
training_quality_score: Integer  # 0-100
last_training_at: DateTime
```

### BrandDocument Model
```python
# New fields added:
language: String(10)  # default "en"
source_url: String(500)
file_name: String(200)
relevance_score: Integer  # default 100
last_retrieved_at: DateTime
is_active: Boolean  # default True
```

## Dissertation Alignment

These enhancements directly support the research objectives:

1. **Human-AI Hybrid Design**: Quality scores and recommendations keep humans in control
2. **SME Accessibility**: Clear guidance helps resource-constrained teams
3. **Global Reach**: Multi-language support for UK, Nigeria, and beyond
4. **Brand Consistency**: Enhanced fields ensure accurate voice representation
5. **Continuous Improvement**: Usage tracking enables iterative optimization

## Testing the Enhancements

```bash
# Start the server
uvicorn app.main:app --reload

# Visit Swagger UI
http://localhost:8000/docs

# Test endpoints:
1. Create brand profile with enhanced fields
2. Upload documents in multiple languages
3. Check /analysis for quality score
4. Retrieve context with language parameter
5. List and manage documents
```

## Next Steps

The enhanced Brand Voice module is now ready for:
- Content Studio integration (next module)
- Real-world testing with SME users
- Iterative improvements based on usage data
