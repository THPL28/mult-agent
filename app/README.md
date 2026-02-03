# MultiAgent Platform

A world-class **Intelligent Agent Orchestration Platform** with LLM, designed to transform **Anything → MarkItDown → Intelligence → Action**.

## 🧠 Core Concept
The system standardizes all inputs into semantic Markdown, orchestrates specialized agents, and executes actions.

## 🏗 Architecture
- **Dashboard**: Next.js (React) - Real-time visualization and control.
- **API**: FastAPI (Python) - Gateway for agents and orchestrator.
- **Agents**: Python - Application logic for MarkItDown, Embeddings, Orchestration.
- **Vector DB**: Qdrant - Semantic search engine.
- **Queue**: RabbitMQ - Message backbone.
- **Database**: PostgreSQL - Structured data storage.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Node.js & npm (for local dashboard dev)
- Python 3.11+ (for local api dev)

### Run Everything with Docker
```bash
cd multiagent/docker
docker-compose up --build
```

### Local Development

#### API
```bash
cd multiagent/api
pip install -r requirements.txt
python main.py
```

#### Dashboard
```bash
cd multiagent/dashboard
npm install
npm run dev
```

## 📂 Structure
- `/agents`: Source code for specialized agents.
- `/api`: FastAPI backend.
- `/dashboard`: Next.js frontend.
- `/docker`: Infrastructure definitions.
- `/vector_db`: Vector database configs.

## License
Proprietary / Enterprise.
