# 🚀 GraftAI - AI-Powered Scheduling Platform

> **Production Ready** | **Dark Theme** | **Secure** | **Fast**

GraftAI is a high-performance, AI-powered scheduling platform that unifies your digital calendar ecosystem with intelligent automation.

## ✨ Features

- 🤖 **AI Scheduling Intelligence** - Smart meeting coordination and optimization
- 🔄 **Universal Calendar Sync** - Google Calendar & Microsoft Outlook integration
- 🎨 **Modern Dark UI** - Beautiful, responsive interface optimized for productivity
- 🔒 **Enterprise Security** - OAuth 2.0, JWT authentication, encrypted data
- ⚡ **High Performance** - Built with FastAPI and Next.js for blazing speed
- 📱 **Mobile Responsive** - Works seamlessly on all devices
- 🌐 **PWA Support** - Install as a native app

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with async SQLAlchemy
- **Cache**: Redis for session management
- **AI**: OpenAI GPT-4 / Groq LLaMA integration
- **Auth**: JWT + OAuth 2.0 (Google, Microsoft)

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS 4
- **Animations**: Framer Motion
- **State**: React Hooks + Context API
- **PWA**: Serwist for offline support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/graftai.git
   cd graftai
   ```

2. **Backend Setup**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your credentials
   pip install -r requirements.txt
   uvicorn api.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   cp .env.example .env.local
   # Edit .env.local with your API URL
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🌐 Production Deployment

### Live URLs
- **Frontend**: https://www.graftai.tech
- **Backend API**: https://graftai.onrender.com
- **API Documentation**: https://graftai.onrender.com/docs

### Deployment Guides
- 📖 [Complete Deployment Guide](./DEPLOYMENT_GUIDE.md)
- 🔒 [Security Audit & Checklist](./SECURITY_AUDIT.md)

### Quick Deploy

#### Backend (Render)
```bash
# Automatic deployment on push to main
git push origin main
```

#### Frontend (Vercel)
```bash
# Automatic deployment on push to main
git push origin main
```

## 🔐 Security

- ✅ HTTPS enforced everywhere
- ✅ Secure JWT authentication
- ✅ OAuth 2.0 with Google & Microsoft
- ✅ CORS restricted to production domains
- ✅ SQL injection protection
- ✅ XSS prevention
- ✅ CSRF protection
- ✅ Rate limiting enabled
- ✅ Secure cookie configuration

See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for complete security documentation.

## 📚 API Documentation

### Authentication Endpoints
```
POST   /api/v1/auth/register          - Create new account
POST   /api/v1/auth/login             - Email/password login
POST   /api/v1/auth/refresh           - Refresh access token
GET    /api/v1/auth/check             - Validate token
GET    /api/v1/auth/google/login      - Google OAuth
GET    /api/v1/auth/microsoft/login   - Microsoft OAuth
```

### Calendar Endpoints
```
GET    /api/v1/calendar/events        - List events
POST   /api/v1/calendar/events        - Create event
GET    /api/v1/calendar/sync          - Sync calendars
```

### AI Endpoints
```
POST   /api/v1/ai/schedule            - AI scheduling
GET    /api/v1/ai/suggestions         - Get AI suggestions
```

Full API documentation available at: https://graftai.onrender.com/docs

## 🎨 UI Components

The application features a modern dark theme with:
- Glassmorphism effects
- Smooth animations
- Responsive design
- Accessible components
- Touch-optimized mobile UI

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Tech Stack

### Backend Dependencies
- `fastapi` - Modern web framework
- `sqlalchemy` - ORM for database
- `pydantic` - Data validation
- `python-jose` - JWT handling
- `authlib` - OAuth implementation
- `redis` - Caching layer
- `openai` - AI integration

### Frontend Dependencies
- `next` - React framework
- `framer-motion` - Animations
- `tailwindcss` - Styling
- `lucide-react` - Icons
- `serwist` - PWA support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Environment Variables

### Backend (.env)
```env
ENV=production
DEBUG=false
BACKEND_URL=https://graftai.onrender.com
FRONTEND_URL=https://www.graftai.tech
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
SECRET_KEY=<generate-secure-key>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
MICROSOFT_CLIENT_ID=<your-microsoft-client-id>
MICROSOFT_CLIENT_SECRET=<your-microsoft-client-secret>
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://graftai.onrender.com
NEXT_PUBLIC_API_BASE_URL=https://graftai.onrender.com/api/v1
NEXT_PUBLIC_APP_URL=https://www.graftai.tech
```

## 🐛 Troubleshooting

### OAuth Redirect Issues
Ensure OAuth provider redirect URIs match:
- Google: `https://graftai.onrender.com/api/v1/auth/google/callback`
- Microsoft: `https://graftai.onrender.com/api/v1/auth/microsoft/callback`

### CORS Errors
Verify `FRONTEND_URL` is set correctly in backend environment.

### Build Failures
Check logs in Render/Vercel dashboard for specific errors.

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## 📊 Performance

- ⚡ API response time: < 100ms average
- 🚀 Frontend load time: < 2s
- 📱 Lighthouse score: 95+
- 🔄 Real-time sync: < 5s latency

## 🗺️ Roadmap

- [ ] Mobile native apps (iOS/Android)
- [ ] Zoom integration
- [ ] Team collaboration features
- [ ] Advanced AI scheduling algorithms
- [ ] Calendar analytics dashboard
- [ ] Email integration
- [ ] Slack/Teams notifications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing backend framework
- Next.js team for the incredible frontend framework
- Vercel for hosting
- Render for backend hosting
- All open-source contributors

## 📧 Contact

- **Website**: https://www.graftai.tech
- **Email**: support@graftai.tech
- **Issues**: https://github.com/yourusername/graftai/issues

---

**Built with ❤️ by the GraftAI Team**

*Making scheduling intelligent, one meeting at a time.*
