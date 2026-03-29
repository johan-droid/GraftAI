<div align="center">
  <br />
  <img src="https://img.shields.io/badge/GraftAI-NEXT--GEN-7C3AED?style=for-the-badge&logo=probot&logoColor=white" alt="GraftAI Logo" />
  <br />
  <h1 align="center"><b>🌌 GraftAI: The Sovereign Orchestration Layer</b></h1>
  <p align="center">
    <b>A High-Fidelity, AI-First Autonomous Engine for Modern Enterprise Workflows.</b><br />
    <i>Sovereign identity, proactive intelligence, and high-performance cross-continental scheduling.</i>
  </p>
  
  <p align="center">
    <img src="https://img.shields.io/github/license/johan-droid/GraftAI?style=flat-square&color=7C3AED" alt="License" />
    <img src="https://img.shields.io/github/v/release/johan-droid/GraftAI?style=flat-square&color=7C3AED" alt="Release" />
    <img src="https://img.shields.io/github/stars/johan-droid/GraftAI?style=flat-square&color=7C3AED" alt="Stars" />
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" />
  </p>

  <br />
</div>

---

## 💎 The Vision
**GraftAI** is a premium, autonomous calendar layer that "grafts" high-fidelity AI directly into your executive stack. Designed for high-performance teams, it replaces chaotic coordination with silent, proactive orchestration.

### ✨ SaaS-Grade Features
- **Proactive AI Agent**: An autonomous LLM engine (Groq/Llama-3.3) that anticipates your scheduling needs.
- **Strong Calendar Connections**: Persistent, enterprise-grade OAuth for Google and Microsoft ecosystems.
- **Sovereign AI Memory**: Local-first vector RAG (Pinecone + HuggingFace) for private, zero-latency context recall.
- **Deep Zoom Integration**: SaaS-grade, user-level token persistence with AES-256 encryption.
- **The Obsidian Interface**: A high-fidelity, glassmorphic nocturnal UI (Next.js 15) optimized for deep focus.
- **Autonomous Notifications**: Real-time SMTP and OneSignal push integration for meeting lifecycle events.

---

## 🏗️ Premium Architecture

```mermaid
graph TD
    subgraph "High-Fidelity Edge"
        UI["Next.js 15 (Nocturnal UI)"]
        AUTH["Sovereign SSO/MFA"]
    end

    subgraph "Autonomous Core"
        API["FastAPI Async Engine"]
        ZOOM["Zoom SaaS Service"]
        AGNT["Proactive AI (LangChain / Groq)"]
    end

    subgraph "Persistence Layer"
        POSTGRES["PostgreSQL 16 (AES-256 Tokens)"]
        REDIS["Redis (Rate-Limit & Cache)"]
        VECTOR["Pinecone (Context Memory)"]
    end

    UI -->|Async Requests| API
    API -->|Orchestrate| AGNT
    API -->|Manage| ZOOM
    API -->|Persist| POSTGRES
    API -->|Cache| REDIS
    AGNT -->|Recall| VECTOR
```

---

## 🚀 Rapid Deployment

### 1. Requirements
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Environment keys (Groq, OpenAI, Pinecone, Zoom)

### 2. Local Setup
```bash
# Clone and enter
git clone https://github.com/johan-droid/GraftAI.git
cd GraftAI

# Configure Core
cp backend/.env.example backend/.env

# High-Performance Backend
cd backend && pip install -r requirements.txt
python app.py

# Modern Frontend
cd ../frontend && npm install
npm run dev
```

### 3. Docker Orchestration
```bash
docker-compose up --build
```

---

## ⚙️ Technical Core (Architectural Evolution)
GraftAI has transitioned to a **Standalone Better Auth** implementation for maximum sovereignty and direct database integration.

### Authentication Strategy
- **Sovereign Control**: Full session lifecycle management without third-party proxies.
- **Biometric Integration**: Native support for FIDO2/Passkey via WebAuthn.
- **Multi-Tenant Identity**: Secure mapping of OAuth accounts (Google, GitHub, Microsoft, Apple) to internal user records.

### Database Architecture
- **Neon Postgres**: Direct connectivity via `pg.Pool` for sub-millisecond latency.
- **SQLAlchemy 2.0**: Asynchronous backend persistence with high-performance connection pooling.
- **Vector Memory**: Pinecone-backed RAG for long-term AI context and recall.

---

## 🛡️ Security Posture
GraftAI implements a **Zero-Trust Security Framework**:
*   **Encrypted Secrets**: All OAuth and Zoom tokens are encrypted at rest using AES-256 bit Fernet logic.
*   **HttpOnly Isolation**: JWTs are strictly isolated from client-side script access.
*   **Granular Privacy**: AI agents operate within isolated multi-tenant contexts to ensure absolute data sovereignty.

---

<div align="center">
  <p><b>Built for the future of work by the Graft Research Labs.</b></p>
  <img src="https://img.shields.io/badge/STATUS-OPERATIONAL-success?style=flat-square" />
</div>
-success?style=flat-square" />
</div>
