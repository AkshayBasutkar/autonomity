# Autonomity - Agentic Honeypot API

An intelligent AI-powered honeypot system designed to detect and engage with scam attempts through automated conversation. The system uses adaptive personas and intelligent agents to interact with scammers while extracting valuable threat intelligence.

## 🎯 Overview

Autonomity is an agentic honeypot API that simulates realistic victims of scam attempts. It automatically detects scam patterns in messages and engages scammers in conversation using AI-powered personas. The system gathers intelligence about scam operations including phishing links, UPI IDs, phone numbers, and bank accounts while maintaining realistic human-like interactions.

## 🌟 Key Features

### Intelligent Scam Detection
- **Multi-layered Detection**: Combines keyword analysis, pattern matching, and LLM-based classification
- **Real-time Scoring**: Dynamic scam score calculation based on urgency, threats, and sensitive information requests
- **Scam Type Classification**: Identifies specific scam types (bank fraud, UPI scams, phishing, fake offers)
- **LLM Integration**: Optional Groq API integration for enhanced scam detection using large language models

### Adaptive AI Agent
- **Dynamic Personas**: Four distinct personas (young professional, small business owner, student, retired person)
- **Phase-based Conversation**: Progresses through trust-building, elicitation, extraction, and exit phases
- **Memory System**: Tracks scammer claims, requested information, and communication channels
- **Context-aware Responses**: Generates realistic responses based on conversation history and persona

### Intelligence Extraction
- **Bank Account Numbers**: Detects and extracts account numbers (9-18 digits)
- **UPI IDs**: Identifies Indian UPI payment identifiers
- **Phishing Links**: Captures suspicious URLs
- **Phone Numbers**: Extracts phone numbers from messages
- **Suspicious Keywords**: Tracks urgency indicators, threats, and sensitive requests

### Session Management
- **Redis-based Storage**: Persistent session storage for conversation continuity
- **Conversation History**: Maintains full conversation context
- **Engagement Metrics**: Tracks duration and message counts
- **Auto-completion**: Sessions complete based on message count or exit phase

## 🏗️ Architecture

```
├── app/
│   ├── agent/           # AI agent with persona management
│   ├── api/             # FastAPI routes and endpoints
│   ├── config/          # Application settings
│   ├── core/            # Core business logic (message handler)
│   ├── detection/       # Scam detection engine
│   │   ├── scam_detector.py    # Pattern-based detection
│   │   └── llm_classifier.py   # LLM-based classification
│   ├── intelligence/    # Information extraction
│   ├── models/          # Pydantic schemas
│   └── services/        # External services (Redis, callbacks)
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── .env.example         # Environment configuration template
```

## 📋 Prerequisites

- Python 3.9+
- Redis server
- (Optional) Groq API key for LLM-enhanced detection

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/AkshayBasutkar/autonomity.git
cd autonomity
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
API_SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key  # Optional
MODEL_NAME=llama-3.1-70b-versatile
REDIS_URL=redis://localhost:6379
GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult
LOG_LEVEL=INFO
LLM_DETECTION_ENABLED=true
LLM_WEIGHT=40
```

4. **Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or using local Redis
redis-server
```

5. **Run the application**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```

Returns service health status.

**Response:**
```json
{
  "status": "ok"
}
```

### Send Message
```http
POST /api/message
```

Processes a message from a potential scammer and generates an agent response.

**Headers:**
- `X-Api-Key`: Your API secret key

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Your account will be blocked! Send OTP immediately.",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "whatsapp",
    "language": "en",
    "locale": "en-IN"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "scamDetected": true,
  "engagementMetrics": {
    "engagementDurationSeconds": 120,
    "totalMessagesExchanged": 5
  },
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": ["scammer@paytm"],
    "phishingLinks": ["https://fake-bank.com/verify"],
    "phoneNumbers": ["9876543210"],
    "suspiciousKeywords": ["urgent", "otp", "blocked"]
  },
  "agentNotes": "Scammer used urgency or sensitive info request patterns.",
  "agentResponse": "Oh no! What happened? Why will it be blocked?"
}
```

### Get Session
```http
GET /api/session/{session_id}
```

Retrieves session information.

**Headers:**
- `X-Api-Key`: Your API secret key

**Response:**
```json
{
  "sessionId": "unique-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 8,
  "phase": "extract",
  "completed": false
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_SECRET_KEY` | Secret key for API authentication | Required |
| `GROQ_API_KEY` | Groq API key for LLM features | Optional |
| `MODEL_NAME` | Groq model name | `llama-3.1-70b-versatile` |
| `REDIS_URL` | Redis connection URL | Required |
| `GUVI_CALLBACK_URL` | Callback URL for final results | Optional |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LLM_DETECTION_ENABLED` | Enable LLM-based detection | `true` |
| `LLM_WEIGHT` | Weight for LLM confidence score | `40` |

### Settings Configuration

Additional settings can be configured in `app/config/settings.py`:
- `scam_score_threshold`: Minimum score to flag as scam (default: 50)
- `max_messages_per_session`: Maximum messages before auto-completion (default: 20)

## 🎭 Personas

The system uses four distinct personas that adapt to different scam types:

1. **Aarav (Young Professional)**: 28, tech support associate, casual and slightly anxious
2. **Meera (Small Business Owner)**: 42, runs a retail store, polite and practical
3. **Rohan (Student)**: 21, college student, informal and confused
4. **Kavita (Retired)**: 63, retired teacher, formal and cautious

Personas are automatically selected based on the detected scam type.

## 🔄 Conversation Phases

1. **Trust Phase** (Messages 1-3): Building initial rapport
2. **Elicit Phase** (Messages 4-9): Asking questions to gather scammer details
3. **Extract Phase** (Messages 10-15): Actively extracting threat intelligence
4. **Exit Phase** (16+ or after intelligence gathered): Gracefully ending conversation

## 🛡️ Security

- API key authentication required for all endpoints
- No real sensitive information is shared with scammers
- Session data stored securely in Redis
- Optional integration with external callback systems

## 🔍 Scam Detection Methods

1. **Keyword Analysis**: Urgency, threats, sensitive requests, rewards
2. **Pattern Matching**: URLs, UPI IDs, phone numbers, bank accounts
3. **Scoring System**: Weighted scoring based on risk indicators
4. **LLM Classification**: Optional AI-powered scam classification (when enabled)

## 📊 Use Cases

- **Scam Research**: Gather intelligence on active scam operations
- **Threat Intelligence**: Extract IOCs (phishing links, phone numbers, accounts)
- **Pattern Analysis**: Identify emerging scam tactics and techniques
- **Security Training**: Understand social engineering methods
- **Honeypot Deployment**: Attract and analyze scammer behavior

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

This project is provided as-is for educational and research purposes.

## ⚠️ Disclaimer

This tool is designed for research and security purposes. Always operate within legal boundaries and obtain proper authorization before deploying honeypot systems.
