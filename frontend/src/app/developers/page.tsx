/**
 * Developer Hub Page
 * 
- Full documentation browser
- Code examples and snippets
- API explorer
- Quick start guides
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import Link from 'next/link';
import { 
  Code2, Terminal, FileText, BookOpen, 
  Zap, GitBranch, Cpu, Layers, ArrowRight,
  ExternalLink, Copy, CheckCircle2, Search,
  ChevronRight, ChevronDown, Menu, X,
  Globe, KeyRound, Database, Webhook,
  Smartphone, Palette, Box, Shield
} from 'lucide-react';

const docSections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: <Zap className="w-5 h-5" />,
    items: [
      { title: 'Quick Start Guide', href: '#quick-start', description: 'Get up and running in 5 minutes' },
      { title: 'Installation', href: '#installation', description: 'Setup your development environment' },
      { title: 'Authentication', href: '#authentication', description: 'Standard OAuth 2.0 flow' },
      { title: 'First API Call', href: '#first-call', description: 'Make your first booking' },
    ]
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    icon: <Webhook className="w-5 h-5" />,
    items: [
      { title: 'Bookings API', href: '#bookings', description: 'Create, update, delete bookings' },
      { title: 'Calendar Sync', href: '#calendar', description: 'Google & Outlook integration' },
      { title: 'Team Management', href: '#teams', description: 'Round-robin and collective scheduling' },
      { title: 'Analytics', href: '#analytics', description: 'Metrics and reporting endpoints' },
      { title: 'Webhooks', href: '#webhooks', description: 'Real-time event notifications' },
    ]
  },
  {
    id: 'frontend',
    title: 'Frontend Docs',
    icon: <Palette className="w-5 h-5" />,
    items: [
      { title: 'Component Library', href: '#components', description: 'React components and hooks' },
      { title: 'Design System', href: '#design', description: 'Colors, typography, spacing' },
      { title: 'Animations', href: '#animations', description: 'Framer Motion patterns' },
      { title: 'Offline Mode', href: '#offline', description: 'IndexedDB and sync patterns' },
    ]
  },
  {
    id: 'sdks',
    title: 'SDKs & Tools',
    icon: <Box className="w-5 h-5" />,
    items: [
      { title: 'JavaScript SDK', href: '#js-sdk', description: 'npm install @graftai/sdk' },
      { title: 'Python SDK', href: '#python-sdk', description: 'pip install graftai' },
      { title: 'CLI Tool', href: '#cli', description: 'Command line interface' },
      { title: 'Postman Collection', href: '#postman', description: 'Pre-configured API tests' },
    ]
  },
  {
    id: 'advanced',
    title: 'Advanced Topics',
    icon: <Cpu className="w-5 h-5" />,
    items: [
      { title: 'Rate Limiting', href: '#rate-limits', description: 'Understanding API limits' },
      { title: 'Error Handling', href: '#errors', description: 'Best practices for resilience' },
      { title: 'Security', href: '#security', description: 'GDPR, encryption, compliance' },
      { title: 'Performance', href: '#performance', description: 'Optimization techniques' },
    ]
  },
];

const codeExamples = {
  javascript: `import { GraftAI } from '@graftai/sdk';

const graft = new GraftAI({
  accessToken: 'your_access_token'
});

// Create a booking
const booking = await graft.bookings.create({
  title: 'Team Sync',
  startTime: '2025-04-15T10:00:00Z',
  endTime: '2025-04-15T11:00:00Z',
  attendee: {
    email: 'colleague@company.com',
    name: 'Jane Smith'
  }
});

console.log('Booking created:', booking.id);`,

  python: `from graftai import GraftAI

graft = GraftAI(access_token='your_access_token')

# Create a booking
booking = graft.bookings.create(
    title='Team Sync',
    start_time='2025-04-15T10:00:00Z',
    end_time='2025-04-15T11:00:00Z',
    attendee={
        'email': 'colleague@company.com',
        'name': 'Jane Smith'
    }
)

print(f'Booking created: {booking.id}')`,

  curl: `curl -X POST https://api.graftai.com/v1/bookings \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Team Sync",
    "start_time": "2025-04-15T10:00:00Z",
    "end_time": "2025-04-15T11:00:00Z",
    "attendee_email": "colleague@company.com"
  }'`
};

export default function DevelopersPage() {
  const [activeSection, setActiveSection] = useState('getting-started');
  const [expandedSections, setExpandedSections] = useState<string[]>(['getting-started']);
  const [activeTab, setActiveTab] = useState<'javascript' | 'python' | 'curl'>('javascript');
  const [copied, setCopied] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleSection = (id: string) => {
    setExpandedSections(prev => 
      prev.includes(id) 
        ? prev.filter(s => s !== id)
        : [...prev, id]
    );
  };

  const copyCode = () => {
    navigator.clipboard.writeText(codeExamples[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredSections = docSections.map(section => ({
    ...section,
    items: section.items.filter(item => 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(section => section.items.length > 0);

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Code2 className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-bold">GraftAI</span>
              <span className="text-slate-500 text-sm">| Developers</span>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/docs/api" className="text-slate-400 hover:text-white transition-colors text-sm">API</Link>
              <Link href="/docs/guide" className="text-slate-400 hover:text-white transition-colors text-sm">Guide</Link>
              <Link href="/docs/frontend" className="text-slate-400 hover:text-white transition-colors text-sm">Frontend</Link>
              <a 
                href="https://github.com/graftai" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors text-sm"
              >
                <GitBranch className="w-4 h-4" />
                GitHub
              </a>
            </nav>

            <div className="hidden md:flex items-center gap-3">
              <Link href="/login">
                <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white text-sm font-medium transition-colors">
                  Sign In
                </button>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-slate-400 hover:text-white"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-slate-800 bg-slate-900"
            >
              <div className="px-4 py-4 space-y-3">
                <Link href="/docs/api" className="block text-slate-300 hover:text-white py-2">API Reference</Link>
                <Link href="/docs/guide" className="block text-slate-300 hover:text-white py-2">Developer Guide</Link>
                <Link href="/docs/frontend" className="block text-slate-300 hover:text-white py-2">Frontend Docs</Link>
                <a 
                  href="https://github.com/graftai" 
                  target="_blank"
                  className="block text-slate-300 hover:text-white py-2"
                >
                  GitHub
                </a>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Build with{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              GraftAI
            </span>
          </h1>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
            Comprehensive documentation, API references, and developer tools to integrate 
            intelligent scheduling into your applications.
          </p>

          {/* Search */}
          <div className="max-w-xl mx-auto relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-[280px,1fr] gap-8">
          {/* Sidebar Navigation */}
          <motion.aside
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="hidden lg:block"
          >
            <div className="sticky top-24 space-y-2">
              {filteredSections.map((section) => (
                <div key={section.id} className="rounded-lg overflow-hidden">
                  <button
                    onClick={() => toggleSection(section.id)}
                    className="w-full flex items-center justify-between p-3 text-left hover:bg-slate-900/50 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-indigo-400">{section.icon}</span>
                      <span className="font-medium text-slate-300">{section.title}</span>
                    </div>
                    <ChevronDown 
                      className={`w-4 h-4 text-slate-500 transition-transform ${
                        expandedSections.includes(section.id) ? 'rotate-180' : ''
                      }`} 
                    />
                  </button>
                  
                  <AnimatePresence>
                    {expandedSections.includes(section.id) && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="pl-10 pr-2 pb-2 space-y-1">
                          {section.items.map((item) => (
                            <button
                              key={item.href}
                              onClick={() => setActiveSection(item.href)}
                              className={`w-full text-left p-2 rounded-lg text-sm transition-colors ${
                                activeSection === item.href
                                  ? 'bg-indigo-500/10 text-indigo-400'
                                  : 'text-slate-400 hover:text-white hover:bg-slate-900/50'
                              }`}
                            >
                              {item.title}
                            </button>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </motion.aside>

          {/* Main Content */}
          <main className="min-h-[600px]">
            {/* Code Example Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mb-12"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Quick Start</h2>
                <Link 
                  href="/docs/guide/quick-start" 
                  className="text-indigo-400 hover:text-indigo-300 text-sm flex items-center gap-1"
                >
                  View full guide <ArrowRight className="w-4 h-4" />
                </Link>
              </div>

              {/* Code Tabs */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="flex items-center border-b border-slate-800">
                  {(['javascript', 'python', 'curl'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`px-4 py-3 text-sm font-medium capitalize transition-colors ${
                        activeTab === tab
                          ? 'text-indigo-400 border-b-2 border-indigo-400 bg-indigo-500/5'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {tab === 'curl' ? 'cURL' : tab}
                    </button>
                  ))}
                  <div className="flex-1" />
                  <button
                    onClick={copyCode}
                    className="px-4 py-3 text-slate-400 hover:text-white flex items-center gap-2 text-sm transition-colors"
                  >
                    {copied ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-green-400" />
                        <span className="text-green-400">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
                
                <div className="p-4 overflow-x-auto">
                  <pre className="text-sm font-mono text-slate-300 leading-relaxed">
                    <code>{codeExamples[activeTab]}</code>
                  </pre>
                </div>
              </div>
            </motion.div>

            {/* Documentation Cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="grid sm:grid-cols-2 gap-4"
            >
              {filteredSections.flatMap(s => s.items).slice(0, 6).map((item, index) => (
                <motion.div
                  key={item.href}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                >
                  <Link href={item.href}>
                    <motion.div
                      whileHover={{ scale: 1.02, y: -2 }}
                      className="group p-5 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-indigo-500/30 transition-all"
                    >
                      <h3 className="font-semibold text-white mb-1 group-hover:text-indigo-400 transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-slate-400 text-sm">{item.description}</p>
                      <div className="mt-3 flex items-center gap-1 text-indigo-400 text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                        Read more <ChevronRight className="w-4 h-4" />
                      </div>
                    </motion.div>
                  </Link>
                </motion.div>
              ))}
            </motion.div>

            {/* Resources Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="mt-12"
            >
              <h2 className="text-xl font-bold text-white mb-4">Developer Resources</h2>
              <div className="grid sm:grid-cols-3 gap-4">
                {[
                  { 
                    icon: <FileText className="w-6 h-6" />, 
                    title: 'API Reference',
                    desc: 'Complete endpoint documentation',
                    href: '/docs/api',
                    color: 'from-blue-500 to-cyan-500'
                  },
                  { 
                    icon: <BookOpen className="w-6 h-6" />, 
                    title: 'Developer Guide',
                    desc: 'Integration tutorials',
                    href: '/docs/guide',
                    color: 'from-purple-500 to-pink-500'
                  },
                  { 
                    icon: <Layers className="w-6 h-6" />, 
                    title: 'Frontend Docs',
                    desc: 'Component library & design',
                    href: '/docs/frontend',
                    color: 'from-orange-500 to-red-500'
                  },
                ].map((resource) => (
                  <Link key={resource.title} href={resource.href}>
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="group p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-all"
                    >
                      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-r ${resource.color} mb-3`}>
                        {resource.icon}
                      </div>
                      <h3 className="font-semibold text-white mb-1">{resource.title}</h3>
                      <p className="text-slate-400 text-sm">{resource.desc}</p>
                    </motion.div>
                  </Link>
                ))}
              </div>
            </motion.div>

            {/* Support CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="mt-12 p-6 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-white mb-1">Need help?</h3>
                  <p className="text-slate-400 text-sm">
                    Join our developer community or reach out to our support team.
                  </p>
                </div>
                <div className="flex gap-3">
                  <a 
                    href="https://github.com/graftai/discussions" 
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-white text-sm font-medium transition-colors"
                  >
                    GitHub Discussions
                  </a>
                  <a 
                    href="mailto:dev@graftai.com"
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white text-sm font-medium transition-colors"
                  >
                    Contact Support
                  </a>
                </div>
              </div>
            </motion.div>
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-slate-500 text-sm">
              © 2024 GraftAI. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link href="/privacy" className="text-slate-500 hover:text-white text-sm transition-colors">Privacy</Link>
              <Link href="/terms" className="text-slate-500 hover:text-white text-sm transition-colors">Terms</Link>
              <a 
                href="https://status.graftai.com" 
                target="_blank"
                className="text-slate-500 hover:text-white text-sm transition-colors flex items-center gap-1"
              >
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                API Status
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
