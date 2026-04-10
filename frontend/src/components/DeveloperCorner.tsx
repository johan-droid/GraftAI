/**
 * Developer Corner Section
 * 
- Vibrant developer-focused design
- Smooth buttery animations
- Links to documentation
- Integrated into landing page
 */

'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { 
  Code2, Terminal, FileText, BookOpen, 
  Zap, GitBranch, Cpu, Layers, ArrowRight,
  ExternalLink, Play, Copy, CheckCircle2,
  Webhook, KeyRound, Database, Globe
} from 'lucide-react';
import { useState } from 'react';

const codeSnippet = `// Quick Start - Create a booking
const booking = await fetch('/api/v1/bookings', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    title: 'Team Sync',
    start_time: '2025-04-15T10:00:00Z',
    end_time: '2025-04-15T11:00:00Z',
    attendee_email: 'colleague@company.com'
  }),
});

const data = await booking.json();
console.log('Booking created:', data.id);`;

const features = [
  {
    icon: <Webhook className="w-6 h-6" />,
    title: 'RESTful API',
    description: 'Comprehensive REST API with 100+ endpoints for scheduling, teams, analytics',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: <KeyRound className="w-6 h-6" />,
    title: 'API Keys & Auth',
    description: 'OAuth 2.0, JWT tokens, and API key management with scoped permissions',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: <Database className="w-6 h-6" />,
    title: 'Webhooks',
    description: 'Real-time event notifications for bookings, cancellations, reschedules',
    color: 'from-orange-500 to-red-500',
  },
  {
    icon: <Globe className="w-6 h-6" />,
    title: 'SDKs & Libraries',
    description: 'Official SDKs for JavaScript, Python, Ruby, and community libraries',
    color: 'from-green-500 to-emerald-500',
  },
];

const quickLinks = [
  { 
    title: 'API Reference', 
    href: '/docs/api',
    icon: <FileText className="w-5 h-5" />,
    description: 'Complete endpoint documentation with examples',
    color: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
  },
  { 
    title: 'Developer Guide', 
    href: '/docs/guide',
    icon: <BookOpen className="w-5 h-5" />,
    description: 'Step-by-step integration tutorials and patterns',
    color: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
  },
  { 
    title: 'Frontend Docs', 
    href: '/docs/frontend',
    icon: <Layers className="w-5 h-5" />,
    description: 'Component library, design system, and UI patterns',
    color: 'bg-pink-500/10 text-pink-400 border-pink-500/20'
  },
  { 
    title: 'GitHub', 
    href: 'https://github.com/graftai',
    icon: <GitBranch className="w-5 h-5" />,
    description: 'Open source repositories and examples',
    external: true,
    color: 'bg-orange-500/10 text-orange-400 border-orange-500/20'
  },
];

const stats = [
  { value: '99.9%', label: 'API Uptime' },
  { value: '<50ms', label: 'Avg Response' },
  { value: '10M+', label: 'API Calls/Day' },
  { value: 'v2.1', label: 'Latest Version' },
];

export default function DeveloperCorner() {
  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText(codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950 overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Orbs */}
        <motion.div
          animate={{
            x: [0, 100, 0],
            y: [0, -50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-20 -left-20 w-[600px] h-[600px] bg-indigo-500/20 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{
            x: [0, -100, 0],
            y: [0, 100, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-20 -right-20 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[100px]"
        />
        <motion.div
          animate={{
            x: [0, 50, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-500/10 rounded-full blur-[120px]"
        />

        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

        {/* Floating Code Snippets */}
        <motion.div
          animate={{ y: [0, -20, 0], opacity: [0.1, 0.2, 0.1] }}
          transition={{ duration: 8, repeat: Infinity }}
          className="absolute top-40 left-20 text-indigo-400/20 text-sm font-mono"
        >
          {'const api = new GraftAI()'}
        </motion.div>
        <motion.div
          animate={{ y: [0, -15, 0], opacity: [0.1, 0.2, 0.1] }}
          transition={{ duration: 10, repeat: Infinity, delay: 2 }}
          className="absolute top-60 right-32 text-purple-400/20 text-sm font-mono"
        >
          {'await booking.create()'}
        </motion.div>
        <motion.div
          animate={{ y: [0, -25, 0], opacity: [0.1, 0.2, 0.1] }}
          transition={{ duration: 12, repeat: Infinity, delay: 4 }}
          className="absolute bottom-40 left-40 text-cyan-400/20 text-sm font-mono"
        >
          {'webhook.on("booking.created")'}
        </motion.div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-20"
        >
          <motion.div
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 mb-6"
          >
            <Code2 className="w-4 h-4 text-indigo-400" />
            <span className="text-indigo-300 text-sm font-medium">Developer Corner</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6"
          >
            Build with{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              GraftAI
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-8"
          >
            Powerful APIs, comprehensive documentation, and developer-first tools 
            to integrate intelligent scheduling into your applications.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/developers">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl text-white font-semibold shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-shadow"
              >
                <Terminal className="w-5 h-5" />
                Explore Developer Hub
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </motion.button>
            </Link>
            <Link href="/docs/api">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-8 py-4 bg-white/10 backdrop-blur-sm rounded-xl text-white font-semibold border border-white/20 hover:bg-white/20 transition-colors"
              >
                <BookOpen className="w-5 h-5" />
                API Reference
              </motion.button>
            </Link>
          </motion.div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-20"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.7 + index * 0.1 }}
              whileHover={{ scale: 1.05, y: -5 }}
              className="p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 text-center"
            >
              <motion.div
                initial={{ opacity: 0, scale: 0 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.8 + index * 0.1, type: 'spring' }}
                className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2"
              >
                {stat.value}
              </motion.div>
              <div className="text-slate-400 text-sm">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Code Preview */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8 }}
          className="max-w-3xl mx-auto mb-20"
        >
          <div className="relative group">
            {/* Glow Effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition-opacity" />
            
            <div className="relative bg-slate-900/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
                <div className="flex items-center gap-2">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <span className="ml-4 text-slate-400 text-sm font-mono">quick-start.js</span>
                </div>
                <button
                  onClick={copyCode}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors text-sm"
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
              
              {/* Code */}
              <div className="p-6 overflow-x-auto">
                <pre className="text-sm sm:text-base font-mono leading-relaxed">
                  <code className="text-slate-300">
                    {codeSnippet.split('\n').map((line, i) => (
                      <div key={i} className="flex">
                        <span className="text-slate-600 select-none w-8 text-right mr-4">
                          {i + 1}
                        </span>
                        <span>
                          {line.includes('//') ? (
                            <>
                              <span className="text-green-400">{line}</span>
                            </>
                          ) : line.includes('const') || line.includes('await') ? (
                            <>
                              <span className="text-purple-400">const</span>
                              <span className="text-blue-400">{' booking'}</span>
                              <span className="text-slate-300">{' = '}</span>
                              <span className="text-purple-400">{'await'}</span>
                              <span className="text-yellow-300">{' fetch'}</span>
                              <span className="text-slate-300">{'('}</span>
                              <span className="text-green-300">{"'/api/v1/bookings'"}</span>
                              <span className="text-slate-300">{', {'}</span>
                            </>
                          ) : (
                            line
                          )}
                        </span>
                      </div>
                    ))}
                  </code>
                </pre>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-20"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 1.1 + index * 0.1 }}
              whileHover={{ y: -10, scale: 1.02 }}
              className="relative group"
            >
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${feature.color} rounded-2xl blur opacity-0 group-hover:opacity-50 transition duration-500`} />
              <div className="relative p-6 bg-slate-900/80 backdrop-blur-sm rounded-2xl border border-slate-700/50 h-full">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-r ${feature.color} mb-4`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Quick Links */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 1.2 }}
          className="grid grid-cols-1 sm:grid-cols-2 gap-4"
        >
          {quickLinks.map((link, index) => (
            <motion.div
              key={link.title}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 1.3 + index * 0.1 }}
            >
              <Link href={link.href} target={link.external ? '_blank' : undefined}>
                <motion.div
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className={`group flex items-center gap-4 p-5 rounded-xl border ${link.color} backdrop-blur-sm transition-all hover:shadow-lg`}
                >
                  <div className="p-2 rounded-lg bg-white/10">
                    {link.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{link.title}</h4>
                      {link.external && <ExternalLink className="w-4 h-4 opacity-50" />}
                    </div>
                    <p className="text-sm opacity-70 mt-0.5">{link.description}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity transform group-hover:translate-x-1" />
                </motion.div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
