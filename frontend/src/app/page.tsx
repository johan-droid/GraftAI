'use client';

import { 
  Box, Button, Container, Typography, Grid, Card, CardContent, AppBar, Toolbar,
  Chip, Avatar, Rating, Stack, Paper, Fade, useTheme, useMediaQuery
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { 
  Sparkles, Calendar, Zap, Shield, Clock, Users, ArrowRight, Check, 
  MessageSquare, Globe, Bell, BarChart3, Smartphone, Rocket,
  Star, Quote, Play, ChevronRight
} from 'lucide-react';
import { useState, useEffect } from 'react';
import DeveloperCorner from '@/components/DeveloperCorner';

export default function Home() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [animatedStats, setAnimatedStats] = useState({ users: 0, meetings: 0, hours: 0 });
  
  // Animate stats on load
  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const interval = duration / steps;
    
    let step = 0;
    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      setAnimatedStats({
        users: Math.floor(50000 * progress),
        meetings: Math.floor(1000000 * progress),
        hours: Math.floor(2500000 * progress),
      });
      if (step >= steps) clearInterval(timer);
    }, interval);
    
    return () => clearInterval(timer);
  }, []);

  const features = [
    {
      icon: <Calendar size={32} />,
      title: 'AI-Powered Scheduling',
      description: 'Intelligent calendar management that learns your preferences and optimizes your time automatically.',
    },
    {
      icon: <Zap size={32} />,
      title: 'Smart Meeting Coordination',
      description: 'Automatically find the best meeting times across time zones with conflict detection and resolution.',
    },
    {
      icon: <Shield size={32} />,
      title: 'Enterprise Security',
      description: 'Bank-grade encryption, SSO authentication, and compliance with SOC 2 and GDPR standards.',
    },
    {
      icon: <Clock size={32} />,
      title: 'Time Analytics',
      description: 'Gain insights into how you spend your time with detailed reports and productivity metrics.',
    },
    {
      icon: <Users size={32} />,
      title: 'Team Collaboration',
      description: 'Seamless team scheduling with shared calendars, availability views, and resource booking.',
    },
    {
      icon: <Sparkles size={32} />,
      title: 'Natural Language AI',
      description: 'Simply tell GraftAI what you need. "Schedule a team sync next Tuesday at 2 PM."',
    },
  ];

  const plans = [
    {
      name: 'Starter',
      price: '$0',
      period: '/month',
      description: 'Perfect for individuals getting started',
      features: ['Up to 100 scheduled events/month', 'Basic AI assistance', 'Email notifications', 'Mobile app access'],
      cta: 'Get Started Free',
      highlighted: false,
    },
    {
      name: 'Professional',
      price: '$19',
      period: '/month',
      description: 'For professionals who need more power',
      features: ['Unlimited scheduled events', 'Advanced AI scheduling', 'Priority support', 'Calendar integrations', 'Team collaboration (up to 5)', 'Custom workflows'],
      cta: 'Start Free Trial',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For organizations with advanced needs',
      features: ['Everything in Professional', 'Unlimited team members', 'SSO & SAML', 'Dedicated support', 'Custom integrations', 'SLA guarantee', 'Advanced analytics'],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)' }}>
      {/* Navigation */}
      <AppBar position="fixed" elevation={0} sx={{ background: 'rgba(15, 15, 26, 0.9)', backdropFilter: 'blur(10px)', borderBottom: '1px solid rgba(99, 102, 241, 0.1)' }}>
        <Container maxWidth="lg">
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ fontWeight: 700, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              GraftAI
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button component={Link} href="#features" sx={{ color: '#94a3b8', textTransform: 'none' }}>Features</Button>
              <Button component={Link} href="#pricing" sx={{ color: '#94a3b8', textTransform: 'none' }}>Pricing</Button>
              <Button component={Link} href="/docs" sx={{ color: '#94a3b8', textTransform: 'none' }}>Docs</Button>
              <Button component={Link} href="/login" variant="contained" sx={{ textTransform: 'none', borderRadius: '8px' }}>Sign In</Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Hero Section */}
      <Container maxWidth="lg" sx={{ pt: { xs: 12, md: 16 }, pb: { xs: 8, md: 12 } }}>
        <Box textAlign="center" maxWidth="900px" mx="auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <Chip
              icon={<Sparkles size={16} />}
              label="AI-Powered Scheduling"
              sx={{
                mb: 3,
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2))',
                color: '#a5b4fc',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                fontWeight: 500,
              }}
            />
            <Typography variant="h1" sx={{ fontSize: { xs: '2.5rem', md: '4rem' }, fontWeight: 800, mb: 3, lineHeight: 1.1 }}>
              Let AI Handle Your{' '}
              <Box component="span" sx={{ background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Calendar Chaos
              </Box>
            </Typography>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}>
            <Typography variant="h5" sx={{ color: '#94a3b8', mb: 4, maxWidth: '700px', mx: 'auto', fontSize: { xs: '1.1rem', md: '1.5rem' } }}>
              GraftAI intelligently manages your schedule, books meetings, and optimizes your time—so you can focus on what matters most.
            </Typography>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button component={Link} href="/register" variant="contained" size="large" sx={{ textTransform: 'none', px: 4, py: 1.5, borderRadius: '12px', fontSize: '1.1rem' }}>
                Start Free Trial <ArrowRight size={20} style={{ marginLeft: 8 }} />
              </Button>
              <Button component={Link} href="#demo" variant="outlined" size="large" sx={{ textTransform: 'none', px: 4, py: 1.5, borderRadius: '12px', fontSize: '1.1rem', borderColor: 'rgba(99, 102, 241, 0.5)' }}>
                Watch Demo
              </Button>
            </Box>
          </motion.div>
        </Box>
      </Container>

      {/* Features Section */}
      <Box id="features" sx={{ py: { xs: 8, md: 12 }, background: 'rgba(26, 26, 46, 0.3)' }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" sx={{ mb: 2, fontWeight: 700, fontSize: { xs: '2rem', md: '3rem' } }}>
            Powerful Features for Modern Teams
          </Typography>
          <Typography variant="body1" textAlign="center" sx={{ color: '#94a3b8', mb: 8, maxWidth: '600px', mx: 'auto' }}>
            Everything you need to manage your time effectively, powered by cutting-edge AI technology.
          </Typography>

          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.1 }} viewport={{ once: true }}>
                  <Card sx={{ height: '100%', background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99, 102, 241, 0.1)', '&:hover': { borderColor: 'rgba(99, 102, 241, 0.3)', transform: 'translateY(-4px)' }, transition: 'all 0.3s ease' }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box sx={{ color: '#6366f1', mb: 2 }}>{feature.icon}</Box>
                      <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>{feature.title}</Typography>
                      <Typography variant="body2" sx={{ color: '#94a3b8' }}>{feature.description}</Typography>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Box sx={{ py: { xs: 8, md: 12 }, background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%)' }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            {[
              { icon: Users, label: 'Active Users', value: animatedStats.users.toLocaleString() },
              { icon: Calendar, label: 'Meetings Booked', value: animatedStats.meetings.toLocaleString() },
              { icon: Clock, label: 'Hours Saved', value: animatedStats.hours.toLocaleString() },
            ].map((stat, index) => (
              <Grid item xs={12} md={4} key={index}>
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.1 }} viewport={{ once: true }}>
                  <Paper sx={{ p: 4, background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.6) 0%, rgba(15, 15, 26, 0.8) 100%)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99, 102, 241, 0.2)', textAlign: 'center' }}>
                    <Box sx={{ color: '#6366f1', mb: 2 }}><stat.icon size={32} /></Box>
                    <Typography variant="h3" sx={{ fontWeight: 700, mb: 1, color: '#f8fafc' }}>{stat.value}+</Typography>
                    <Typography variant="body1" sx={{ color: '#94a3b8' }}>{stat.label}</Typography>
                  </Paper>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Box id="testimonials" sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" sx={{ mb: 2, fontWeight: 700, fontSize: { xs: '2rem', md: '3rem' } }}>
            Loved by Teams Worldwide
          </Typography>
          <Typography variant="body1" textAlign="center" sx={{ color: '#94a3b8', mb: 8, maxWidth: '600px', mx: 'auto' }}>
            See what professionals are saying about GraftAI
          </Typography>

          <Grid container spacing={4}>
            {[
              {
                name: 'Sarah Chen',
                role: 'Product Manager at TechCorp',
                avatar: 'SC',
                rating: 5,
                quote: 'GraftAI has completely transformed how our team schedules meetings. The AI suggestions are incredibly accurate.',
              },
              {
                name: 'Michael Roberts',
                role: 'CEO at StartupXYZ',
                avatar: 'MR',
                rating: 5,
                quote: 'I save at least 5 hours every week on scheduling. The ROI has been phenomenal for our organization.',
              },
              {
                name: 'Emily Watson',
                role: 'Engineering Lead at DevCo',
                avatar: 'EW',
                rating: 5,
                quote: 'The calendar sync across Google, Outlook, and Apple is seamless. Finally, a scheduling tool that just works.',
              },
            ].map((testimonial, index) => (
              <Grid item xs={12} md={4} key={index}>
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.1 }} viewport={{ once: true }}>
                  <Card sx={{ height: '100%', background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)', backdropFilter: 'blur(10px)', border: '1px solid rgba(99, 102, 241, 0.1)' }}>
                    <CardContent sx={{ p: 4 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <Avatar sx={{ width: 48, height: 48, mr: 2, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)' }}>
                          {testimonial.avatar}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{testimonial.name}</Typography>
                          <Typography variant="body2" sx={{ color: '#94a3b8', fontSize: '0.875rem' }}>{testimonial.role}</Typography>
                        </Box>
                      </Box>
                      <Rating value={testimonial.rating} readOnly sx={{ mb: 2 }} />
                      <Typography variant="body1" sx={{ color: '#cbd5e1', fontStyle: 'italic' }}>"{testimonial.quote}"</Typography>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box sx={{ py: { xs: 8, md: 12 }, background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)' }}>
        <Container maxWidth="lg">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} viewport={{ once: true }}>
            <Box textAlign="center" maxWidth="700px" mx="auto">
              <Typography variant="h3" sx={{ fontWeight: 700, mb: 3, fontSize: { xs: '1.75rem', md: '2.5rem' } }}>
                Ready to Transform Your Scheduling?
              </Typography>
              <Typography variant="body1" sx={{ color: '#94a3b8', mb: 6 }}>
                Join thousands of professionals who save hours every week with GraftAI's AI-powered scheduling.
              </Typography>
              <Button component={Link} href="/register" variant="contained" size="large" sx={{ textTransform: 'none', px: 6, py: 2, borderRadius: '12px', fontSize: '1.2rem' }}>
                Get Started Free <ArrowRight size={24} style={{ marginLeft: 12 }} />
              </Button>
            </Box>
          </motion.div>
        </Container>
      </Box>

      {/* Pricing Section */}
      <Box id="pricing" sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="lg">
          <Typography variant="h2" textAlign="center" sx={{ mb: 2, fontWeight: 700, fontSize: { xs: '2rem', md: '3rem' } }}>
            Simple, Transparent Pricing
          </Typography>
          <Typography variant="body1" textAlign="center" sx={{ color: '#94a3b8', mb: 8, maxWidth: '600px', mx: 'auto' }}>
            Choose the plan that fits your needs. All plans include core AI scheduling features.
          </Typography>

          <Grid container spacing={4} alignItems="stretch">
            {plans.map((plan, index) => (
              <Grid item xs={12} md={4} key={index}>
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: index * 0.1 }} viewport={{ once: true }} style={{ height: '100%' }}>
                  <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', background: plan.highlighted ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)' : 'linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)', backdropFilter: 'blur(10px)', border: plan.highlighted ? '2px solid #6366f1' : '1px solid rgba(99, 102, 241, 0.1)', position: 'relative', overflow: 'visible' }}>
                    {plan.highlighted && (
                      <Box sx={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', color: 'white', px: 2, py: 0.5, borderRadius: '20px', fontSize: '0.75rem', fontWeight: 600 }}>
                        MOST POPULAR
                      </Box>
                    )}
                    <CardContent sx={{ p: 4, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                      <Typography variant="h5" sx={{ mb: 1, fontWeight: 600 }}>{plan.name}</Typography>
                      <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>{plan.description}</Typography>
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="h3" component="span" sx={{ fontWeight: 700 }}>{plan.price}</Typography>
                        <Typography variant="body2" component="span" sx={{ color: '#94a3b8' }}>{plan.period}</Typography>
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        {plan.features.map((feature, fIndex) => (
                          <Box key={fIndex} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                            <Check size={16} style={{ color: '#10b981', flexShrink: 0 }} />
                            <Typography variant="body2" sx={{ color: '#e2e8f0' }}>{feature}</Typography>
                          </Box>
                        ))}
                      </Box>
                      <Button fullWidth variant={plan.highlighted ? 'contained' : 'outlined'} sx={{ mt: 3, textTransform: 'none', borderRadius: '8px' }}>
                        {plan.cta}
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Developer Corner */}
      <DeveloperCorner />

      {/* Footer */}
      <Box sx={{ py: 8, background: 'rgba(15, 15, 26, 0.8)', borderTop: '1px solid rgba(99, 102, 241, 0.1)' }}>
        <Container maxWidth="lg">
          <Grid container spacing={6}>
            <Grid item xs={12} md={4}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                GraftAI
              </Typography>
              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 3 }}>
                AI-powered scheduling platform that transforms how you manage your time and meetings.
              </Typography>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Product</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Link href="#features" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Features</Link>
                <Link href="#pricing" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Pricing</Link>
                <Link href="/docs" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Documentation</Link>
                <Link href="/developers" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Developers</Link>
                <Link href="/integrations" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Integrations</Link>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Company</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Link href="/about" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>About</Link>
                <Link href="/blog" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Blog</Link>
                <Link href="/careers" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Careers</Link>
                <Link href="/contact" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Contact</Link>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Legal</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Link href="/privacy" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Privacy Policy</Link>
                <Link href="/terms" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Terms of Service</Link>
                <Link href="/security" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Security</Link>
                <Link href="/gdpr" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>GDPR</Link>
              </Box>
            </Grid>
            <Grid item xs={6} md={2}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Support</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Link href="/help" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Help Center</Link>
                <Link href="/api-status" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>API Status</Link>
                <Link href="/changelog" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.875rem' }}>Changelog</Link>
              </Box>
            </Grid>
          </Grid>
          <Box sx={{ mt: 6, pt: 4, borderTop: '1px solid rgba(99, 102, 241, 0.1)', textAlign: 'center' }}>
            <Typography variant="body2" sx={{ color: '#64748b' }}>
              © 2024 GraftAI. All rights reserved. Built with precision for modern professionals.
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}
