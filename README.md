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
  <h2 align="center">✨ Real Feature Showcase</h2>
  <div align="center">
    <img src="file:///C:/Users/sahoo/.gemini/antigravity/brain/94534ed5-57a6-434f-9007-df466a7dfd19/login_page_1774358778006.png" width="45%" style="border-radius: 10px; margin: 5px;" />
    <img src="file:///C:/Users/sahoo/.gemini/antigravity/brain/94534ed5-57a6-434f-9007-df466a7dfd19/register_page_1774358788690.png" width="45%" style="border-radius: 10px; margin: 5px;" />
    <br />
    <img src="file:///C:/Users/sahoo/.gemini/antigravity/brain/94534ed5-57a6-434f-9007-df466a7dfd19/sso_page_1774358801194.png" width="91%" style="border-radius: 10px; margin: 5px;" />
  </div>
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

### 🔐 1. Identity & Sovereignty (Hardened)
* **HttpOnly Cookie Auth**: Production-grade session management using `HttpOnly`, `Secure`, `SameSite=Strict` cookies to mitigate XSS and CSRF risks.
* **Universal SSO**: Native, race-condition-free integration with Google, GitHub, Microsoft, and Apple.
* **Biometric Auth**: Passwordless login using FIDO2/WebAuthn (TouchID/FaceID).
* **Sovereign JWT**: Asynchronous token validation with Auth0 JWKS integration and fail-safe local fallback.

### 🤖 2. Proactive AI Intelligence
* **Contextual Memory**: Powered by RAG (Retrieval Augmented Generation) for long-term user context.
* **Resilient Pinecone**: Advanced vector store integration with robust fallback handling to ensure AI availability during provider outages.
* **Natural Language UI**: Chat-driven scheduling that understands nuances like "find a quick sync before my flight."
* **Advanced RAG**: Strictly isolated multi-tenant indexing for enterprise-grade data privacy.

### 📊 3. Enterprise Observability
* **Live Analytics**: Real-time tracking of meeting health and team productivity.
* **Non-Blocking API**: Fully asynchronous backend orchestration ensuring extreme concurrency and low latency.
* **Multi-Cloud Ready**: Optimized for horizontal scaling with tuned database connection pooling (SQLAlchemy 2.0 Async).

---

## 🏗️ Technical Architecture

```mermaid
graph LR
    subgraph "Hardened Edge"
        UI["Modern UI (Next.js 15+ + Tailwind 4)"]
        Guard["Cookie-Based Auth Middleware"]
    end

    subgraph "Intelligent Core"
        API["FastAPI Async Orchestrator"]
        Auth["Sovereign Identity Service"]
        Agent["Resilient AI Agent (LangChain)"]
    end

    subgraph "Sovereign Persistence"
        RDS["PostgreSQL 16 (Tuned Connection Pool)"]
        VDB["Pinecone (with Fallback)"]
        Cache["Redis (Auth Revocation & Rate Limiting)"]
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
python app.py  # High-performance Uvicorn worker manager
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
*   **HttpOnly Isolation**: JWTs are never exposed to JavaScript, preventing XSS-based account takeovers.
-   **CSRF Hardening**: Enforced `SameSite=Strict` and CORS origin-filtering.
*   **Encrypted Payloads**: All data is encrypted at rest (AES-256) and in transit (TLS 1.3).
*   **Sandboxed AI**: AI agents operate in a restricted environment with limited resource access.
*   **Audit Logging**: Every authentication and database transaction is logged as exception-safe events.

---

<div align="center">
  <p><b>Built for the future of work by GraftAI Labs.</b></p>
  <img src="https://img.shields.io/badge/STATUS-OPERATIONAL-success?style=flat-square" />
</div>
