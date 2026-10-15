# 🎙️ PodCraft — AI Podcast Generator

> 输入一个主题，AI 自动完成心情分析 → 内容规划 → 脚本生成 → 质量审查 → 语音合成 → 音频混音，生成完整播客。

## ✨ Features

- **Multi-Agent Workflow**: Mood Analyzer → Content Planner → Script Writer → Reviewer
- **RAG Knowledge Base**: Upload reference materials via ChromaDB for richer content
- **AI TTS**: 8 built-in voices (Chinese & English) via MiMo TTS
- **BGM Generation**: Auto-generate background music via MiniMax API
- **User Auth & Credits**: JWT authentication with a points/credits system
- **Admin Dashboard**: User management, credit recharge, system stats
- **Modern UI**: Next.js + Tailwind CSS with dark mode, responsive design

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────────────────────────┐
│   Frontend   │     │              Backend                 │
│  (Next.js)   │────▶│  FastAPI + SQLAlchemy + ChromaDB     │
│  Port 3000   │     │  Port 8000                           │
└──────────────┘     │                                      │
                     │  ┌─────────────────────────────────┐ │
                     │  │     Workflow Orchestrator        │ │
                     │  │  ┌───────┐ ┌────────┐ ┌──────┐  │ │
                     │  │  │ Mood  │→│Planner │→│Writer│  │ │
                     │  │  │Analyzer│ │        │ │      │  │ │
                     │  │  └───────┘ └────────┘ └──────┘  │ │
                     │  │       ↓                   ↓      │ │
                     │  │  ┌──────────┐  ┌──────────────┐  │ │
                     │  │  │ Reviewer │  │ TTS + Audio  │  │ │
                     │  │  └──────────┘  └──────────────┘  │ │
                     │  └─────────────────────────────────┘ │
                     │                                      │
                     │  ┌────────┐  ┌──────┐  ┌──────────┐  │
                     │  │PostgreSQL│ │ChromaDB│ │MiniMax  │  │
                     │  └────────┘  └──────┘  └──────────┘  │
                     └──────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 15+ (or Docker)

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/pod_craft_project.git
cd pod_craft_project
```

### 2. Start PostgreSQL (via Docker)

```bash
docker compose up postgres -d
```

### 3. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys

uv sync
uv run uvicorn main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/podcasts/generate` | Create podcast generation task |
| `GET` | `/api/podcasts` | List all podcasts |
| `GET` | `/api/podcasts/:id` | Get podcast detail |
| `DELETE` | `/api/podcasts/:id` | Delete podcast |
| `POST` | `/api/knowledge` | Upload knowledge document |
| `GET` | `/api/knowledge/search` | Search knowledge base |
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/auth/login` | User login |
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/admin/users` | List all users (admin) |
| `POST` | `/api/admin/users/:id/credits` | Add credits (admin) |
| `GET` | `/api/admin/stats` | System stats (admin) |
| `GET` | `/api/health` | Health check |

## 🛠️ Tech Stack

**Backend**: Python 3.13 · FastAPI · SQLAlchemy · PostgreSQL · ChromaDB · Pydantic

**Frontend**: Next.js 14 · React 18 · TypeScript · Tailwind CSS 3 · Framer Motion · Zustand

**AI Services**: DeepSeek LLM · MiMo TTS · MiniMax Music

**DevOps**: Docker Compose · uv · pytest

## 📜 License

MIT
