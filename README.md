# Omni-Agent SaaS

<div align="center">

**Production-Ready Multi-Agent Backend System**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A comprehensive multi-agent SaaS platform featuring CrewAI agents, real-time analytics, conversation memory, and persistent task management.*

</div>

## 🚀 Overview

Omni-Agent SaaS is a production-shaped multi-agent backend system that combines the power of AI agents with enterprise-grade infrastructure. It features three specialized CrewAI agents (Support, Content, Data Analyst) backed by modern architecture including FastAPI, Celery workers, ChromaDB RAG, PostgreSQL persistence, and comprehensive analytics.

### ✨ Key Features

- **🤖 Three Specialized AI Agents**
  - **Support Agent**: Customer support with RAG knowledge base and escalation handling
  - **Content Agent**: Marketing copy generation with web search capabilities
  - **Data Analyst Agent**: Automated data analysis with Excel report generation

- **📊 Real-Time Analytics Dashboard**
  - Usage metrics tracking per agent
  - Latency monitoring (p50, p95, p99 percentiles)
  - Cache performance tracking
  - Popular questions identification
  - Escalation tracking for knowledge base gaps
  - Usage trends over time

- **💬 Conversation Context Memory**
  - Session-based multi-turn dialogues
  - Automatic context injection
  - Configurable history length and TTL
  - Session management APIs

- **📚 Advanced Knowledge Base**
  - Semantic search with ChromaDB
  - Bulk CSV/JSON import support
  - Direct search API for autocomplete
  - Metadata and relevance scoring

- **🗄️ Persistent Task Management**
  - PostgreSQL-based task history
  - Task lifecycle tracking
  - Filterable history and statistics
  - Long-term result persistence

- **🔒 Enterprise-Grade Infrastructure**
  - Redis-based rate limiting with token bucket algorithm
  - Semantic caching for performance optimization
  - Async Celery workers for background processing
  - Health checks and monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Gateway                         │
│                    (api/router.py)                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Support    │      │   Content    │      │   Analyst    │
│    Agent     │      │    Agent     │      │    Agent     │
│  (CrewAI)    │      │  (CrewAI)    │      │  (CrewAI)    │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   ChromaDB   │      │   Web Search │      │   Celery     │
│  (RAG+Cache) │      │   (Serper)   │      │   Workers    │
└──────────────┘      └──────────────┘      └──────────────┘
        │                                           │
        ▼                                           ▼
┌──────────────┐                            ┌──────────────┐
│    Redis     │                            │  PostgreSQL  │
│ (Rate Limit  │                            │ (Task History│
│ + Context)   │                            │ + Analytics) │
└──────────────┘                            └──────────────┘
```

**Technology Stack:**
- **Backend**: FastAPI, Python 3.12+
- **AI Agents**: CrewAI with OpenAI/Anthropic LLMs
- **Vector Database**: ChromaDB for semantic search
- **Cache**: Redis for rate limiting and conversation context
- **Database**: PostgreSQL for persistent task history
- **Task Queue**: Celery with Redis broker
- **Monitoring**: Flower for Celery task monitoring
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** & **Docker Compose** (for containerized deployment)
- **API Key** for one of the following:
  - [OpenAI API Key](https://platform.openai.com/api-keys)
  - [Anthropic API Key](https://console.anthropic.com/)
- **Optional Services**:
  - Gmail/SMTP credentials for email notifications
  - [Serper.dev API Key](https://serper.dev/) for web search functionality

## 🛠️ Installation

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/shadownebulax8-cmd/OmniCore-AI.git
cd OmniCore-AI
```

2. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and set your LLM provider:
```bash
# Choose one: "openai" or "anthropic"
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
# OR
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

3. **Start the services**
```bash
docker compose up --build
```

This will start:
- **FastAPI** application on `http://localhost:8000`
- **ChromaDB** on `http://localhost:8001`
- **Redis** on `localhost:6379`
- **PostgreSQL** on `localhost:5432`
- **Flower** (Celery monitoring) on `http://localhost:5555`

4. **Seed the knowledge base**
```bash
docker compose exec app python main.py seed-kb
```

### Manual Installation

For development or custom deployments:

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start external services**
```bash
# Start Redis, PostgreSQL, and ChromaDB
# (You can use Docker or install them directly)
```

4. **Run the application**
```bash
python main.py serve
```

## 🚀 Usage

### API Endpoints

The system provides RESTful APIs for all agent interactions:

#### Support Agent
```bash
# Ask a question
curl -X POST http://localhost:8000/api/v1/support/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I reset my password?"}'

# Add knowledge base entry
curl -X POST http://localhost:8000/api/v1/support/knowledge \
  -H "Content-Type: application/json" \
  -d '{"text": "Q: Do you support SSO?\nA: Yes, SAML SSO is available on the Enterprise plan."}'

# Bulk import knowledge base
curl -X POST http://localhost:8000/api/v1/support/knowledge/bulk \
  -F "file=@kb_documents.json"

# Search knowledge base directly
curl -X POST http://localhost:8000/api/v1/support/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "password reset", "n_results": 5}'
```

#### Conversation Context
```bash
# Create a conversation session
curl -X POST http://localhost:8000/api/v1/support/session

# Ask with conversation context
curl -X POST http://localhost:8000/api/v1/support/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What about your previous answer?", "session_id": "..."}'

# Get conversation history
curl http://localhost:8000/api/v1/support/session/{session_id}
```

#### Content Generation
```bash
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"content_type":"social_post","platform":"twitter","topic":"our new pricing tier","tone":"excited","audience":"small business owners","max_length":280}'
```

#### Data Analysis
```bash
# Upload file for analysis
curl -X POST http://localhost:8000/api/v1/analyst/upload \
  -F "file=@yourdata.csv"

# Check analysis status
curl http://localhost:8000/api/v1/analyst/status/{task_id}
```

#### Analytics
```bash
# Get daily metrics
curl http://localhost:8000/api/v1/analytics/metrics

# Get latency statistics
curl http://localhost:8000/api/v1/analytics/latency/support

# Get usage trends
curl http://localhost:8000/api/v1/analytics/trends?days=7

# Get escalated questions
curl http://localhost:8000/api/v1/analytics/escalations

# Get popular questions
curl http://localhost:8000/api/v1/analytics/popular-questions
```

#### Task History
```bash
# Get task history
curl http://localhost:8000/api/v1/tasks/history

# Get task statistics
curl http://localhost:8000/api/v1/tasks/statistics

# Get specific task details
curl http://localhost:8000/api/v1/tasks/{task_id}
```

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Celery Monitoring**: `http://localhost:5555`

### CLI Usage

For quick testing without the server:

```bash
# Ask the support bot directly
docker compose exec app python main.py ask "What are your support hours?"

# Seed knowledge base
docker compose exec app python main.py seed-kb
```

## 💡 Benefits

### For Developers
- **Modular Architecture**: Clean separation of concerns with easy-to-extend components
- **Type Safety**: Extensive use of Pydantic for request/response validation
- **Async Processing**: Celery workers for background task handling
- **Comprehensive Testing**: Health checks and validation endpoints
- **Modern Stack**: Latest Python, FastAPI, and AI frameworks

### For Businesses
- **Scalable Infrastructure**: Docker-based deployment with horizontal scaling
- **Cost Optimization**: Semantic caching reduces LLM API calls
- **Analytics Insights**: Real-time metrics for optimization and business intelligence
- **Reliability**: Persistent task history and error handling
- **Flexibility**: Support for multiple LLM providers and easy switching

### For End Users
- **Conversational Experience**: Context-aware multi-turn dialogues
- **Fast Response Times**: Caching and optimized infrastructure
- **Reliable Results**: Escalation handling and knowledge base accuracy
- **Multiple Use Cases**: Support, content creation, and data analysis in one platform

## 📁 Project Structure

```
OmniCore-AI/
├── analytics/              # Real-time analytics and metrics
│   ├── __init__.py
│   └── metrics.py          # Usage tracking and performance monitoring
├── api/                    # FastAPI endpoints
│   ├── __init__.py
│   ├── rate_limiter.py     # Redis-based rate limiting
│   └── router.py           # API route definitions
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Environment-based settings
├── core/                   # AI agent core logic
│   ├── __init__.py
│   ├── agents.py           # CrewAI agent definitions
│   ├── llm_providers.py    # LLM provider abstraction
│   ├── tasks.py            # Agent task definitions
│   └── tools.py            # Agent tools (RAG, web search, etc.)
├── database/               # Database persistence
│   ├── __init__.py
│   └── task_history.py     # PostgreSQL task history management
├── memory/                 # Memory and caching systems
│   ├── __init__.py
│   ├── conversation_context.py  # Session-based conversation memory
│   ├── embedder.py         # Text embedding utilities
│   ├── semantic_cache.py   # Semantic caching layer
│   └── vector_store.py     # ChromaDB vector storage
├── pipeline/               # Data validation and processing
│   ├── __init__.py
│   └── validation.py       # Pydantic models for request/response
├── scripts/                # Utility scripts
│   └── seed_knowledge_base.py  # Knowledge base seeding
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_health.py      # Health check tests
├── workers/                # Background task workers
│   ├── __init__.py
│   ├── celery_app.py       # Celery application configuration
│   ├── email_worker.py     # Email notification tasks
│   └── sheet_worker.py     # Data analysis worker
├── data/                   # Data directories
│   ├── uploads/            # File upload storage
│   └── outputs/            # Generated report storage
├── .dockerignore           # Docker ignore patterns
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore patterns
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai                  # "openai" or "anthropic"
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-5

# Optional: Web Search
SERPER_API_KEY=your_serper_key        # For content agent web search

# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=omni_agent
POSTGRES_PASSWORD=omni_agent_password
POSTGRES_DB=omni_agent_saas

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# ChromaDB Configuration
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# SMTP Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_app_password
SUPPORT_ESCALATION_EMAIL=admin@yourcompany.com

# Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60

# Semantic Cache
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.92

# Conversation Context
CONVERSATION_MAX_HISTORY_LENGTH=10
CONVERSATION_SESSION_TTL_SECONDS=3600
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_health.py
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

## 📊 Monitoring

### Celery Flower
Access the Celery monitoring dashboard at `http://localhost:5555` to:
- Monitor task execution
- View worker status
- Inspect task results
- Track task performance

### Analytics API
Use the analytics endpoints to track:
- Agent usage patterns
- Response latency trends
- Cache hit rates
- Popular questions
- Escalation patterns

## 🚀 Deployment

### Production Considerations

1. **Security**
   - Enable API authentication (JWT/API keys)
   - Use environment variables for secrets
   - Enable HTTPS with SSL certificates
   - Configure firewall rules

2. **Scaling**
   - Scale Celery workers horizontally
   - Use Redis Cluster for high availability
   - Configure PostgreSQL replication
   - Implement load balancing for FastAPI

3. **Monitoring**
   - Set up application monitoring (Prometheus/Grafana)
   - Configure log aggregation (ELK stack)
   - Set up alerting for critical failures
   - Monitor resource usage

4. **Backup**
   - Regular PostgreSQL backups
   - ChromaDB data persistence
   - Redis persistence configuration
   - Disaster recovery planning

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **CrewAI** for the powerful agent framework
- **FastAPI** for the modern web framework
- **ChromaDB** for the vector database
- **Celery** for the task queue system

## 📮 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review the API docs at `/docs` endpoint

---

<div align="center">

**Built with ❤️ using modern Brain and web technologies**

[⭐ Star this repo](https://github.com/shadownebulax8-cmd/OmniCore-AI.git) if it helped you!

</div>
