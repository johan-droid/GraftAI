<div align="center">
  <br />
  <img src="https://img.shields.io/badge/GraftAI-NEXT--GEN-8A2BE2?style=for-the-badge&logo=probot&logoColor=white" alt="GraftAI Logo" />
  <br />
  <h1 align="center"><b>🌌 GraftAI: The Sovereign AI Scheduler</b></h1>
  <p align="center">
    <b>A Enterprise-Ready, AI-First Orchestration Layer for Modern Workflows.</b><br />
    <i>Sovereign identity, proactive intelligence, and high-performance scheduling.</i>
  </p>
  
  <p align="center">
    <img src="https://img.shields.io/github/license/johan-droid/GraftAI?style=flat-square&color=8A2BE2" alt="License" />
    <img src="https://img.shields.io/github/v/release/johan-droid/GraftAI?style=flat-square&color=8A2BE2" alt="Release" />
    <img src="https://img.shields.io/github/stars/johan-droid/GraftAI?style=flat-square&color=8A2BE2" alt="Stars" />
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome" />
  </p>

  <br />
  <img src="file:///C:/Users/sahoo/.gemini/antigravity/brain/94534ed5-57a6-434f-9007-df466a7dfd19/graft_ai_dashboard_mockup_1774358620516.png" width="90%" style="border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.4);" />
  <br />
  <br />
</div>

---

## 💎 The Vision
**GraftAI** isn't just a calendar; it's an **Autonomous Orchestration Layer**. It "grafts" high-fidelity AI directly into your enterprise stack, bridging the gap between raw LLM intelligence and secure, high-stakes business operations.

---

## 🛠️ The Tech Stack

| Layer | Technology | Key Capabilities |
| :--- | :--- | :--- |
| **Frontend** | ![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=flat-square&logo=nextdotjs) | App Router, Server Actions, Framer Motion |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=FastAPI) | Asynchronous Pydantic v2, Dependency Injection |
| **Intelligence** | ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=chainlink) | RAG Workflows, Proactive Agentic Behavior |
| **Identity** | ![Authlib](https://img.shields.io/badge/Identity-SSO_/_FIDO2-FF4F00?style=flat-square) | Google, GitHub, Microsoft, Apple, Passkeys |
| **Storage** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql) | SQLAlchemy 2.0 (Async), High-Performance Migrations |
| **Vector Engine**| ![Pinecone](https://img.shields.io/badge/Pinecone-272727?style=flat-square&logo=pinecone) | Contextual Memory with High-Dimensional Indexing |

---

## 🚀 Core Features

### 🔐 1. Identity & Sovereignty
* **Universal SSO**: Native integration with Google, GitHub, Microsoft, and Apple.
* **Biometric Auth**: Passwordless login using FIDO2/WebAuthn (TouchID/FaceID).
* **Identity Guard**: Multi-factor authentication (TOTP) and proactive session isolation.
* **Cookie-less Magic**: Secure magic link delivery for instant, zero-password access.

### 🤖 2. Proactive AI Intelligence
* **Contextual Memory**: Powered by RAG (Retrieval Augmented Generation) for long-term user context.
* **Proactive Scheduling**: AI doesn't just react; it analyzes patterns and suggests optimized slots.
* **Natural Language UI**: Chat-driven scheduling that understands nuances like "find a quick sync before my flight."
* **Advanced RAG**: Integrated via Pinecone with strict tenant isolation for enterprise data.

### 📊 3. Enterprise Observability
* **Live Analytics**: Real-time tracking of meeting health and team productivity.
* **Proactive Reminders**: Smart notifications that trigger based on context, not just time.
* **Multi-Cloud Ready**: Designed for horizontal scaling across Kubernetes/Docker or Serverless.

---

## 🏗️ Technical Architecture

```mermaid
graph LR
    subgraph "High-Performance Edge"
        UI["Modern UI (Tailwind 4 + Framer)"]
        Guard["Route Guards & JWKS Middleware"]
    end

    subgraph "Intelligent Core"
        API["FastAPI Orchestrator"]
        Auth["Sovereign Identity Service"]
        Agent["AI Agent Service (LangChain)"]
    end

    subgraph "Sovereign Persistence"
        RDS["PostgreSQL 16 (Async IO)"]
        VDB["Pinecone (Serverless)"]
        Cache["Redis (Auth State)"]
    end

    UI --> API
    Guard --> Auth
    API --> Agent
    Agent --> VDB
    Auth --> Cache
    API --> RDS
```

---

## 🛠️ Rapid Setup

### 1. Environment Configuration
Create a `.env` in the `backend/` directory with your premium credentials:
```bash
# Core
DATABASE_URL=postgresql+asyncpg://...
PINECONE_API_KEY=pcsk_...

# AI
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk_...

# Identity (Production URLs)
FRONTEND_BASE_URL=https://graft-ai-two.vercel.app
APP_BASE_URL=https://graftai.onrender.com
```

### 2. Backend Orchestrator
```bash
cd backend
python -m venv .venv
# Activate venv
pip install -r requirements.txt
python app.py  # Wrapper with built-in anti-sleep pinger
```

### 3. Frontend Experience
```bash
cd frontend
npm install
npm run dev
```

---

## 🛡️ Security Posture
GraftAI implements the **Zero-Trust Security Model**:
*   **Encrypted Payloads**: All data is encrypted at rest (AES-256) and in transit (TLS 1.3).
*   **Sandboxed AI**: AI agents operate in a restricted environment with limited resource access.
*   **Strict CORS**: Production-grade origin filtering and header protection.
*   **Audit Logging**: Every authentication event is logged for enterprise compliance.

---

<div align="center">
  <p><b>Built for the future of work by GraftAI Labs.</b></p>
  <img src="https://img.shields.io/badge/STATUS-OPERATIONAL-success?style=flat-square" />
</div>
