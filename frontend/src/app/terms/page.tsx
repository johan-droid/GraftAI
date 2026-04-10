'use client';

import { Box, Container, Typography, Paper } from '@mui/material';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function TermsPage() {
  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)', pt: 8, pb: 8 }}>
      <Container maxWidth="md">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Paper sx={{ p: { xs: 3, md: 6 }, background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 26, 0.98) 100%)', backdropFilter: 'blur(20px)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 4, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Terms of Service
            </Typography>
            
            <Typography variant="body2" sx={{ color: '#64748b', mb: 4 }}>
              Last updated: December 2024
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>1. Acceptance of Terms</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  By accessing or using GraftAI, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our service. GraftAI provides AI-powered scheduling and calendar management services.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>2. Description of Service</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  GraftAI is an intelligent scheduling platform that helps users manage their calendars, schedule meetings, and optimize their time using artificial intelligence. Our service includes calendar synchronization, meeting coordination, time analytics, and AI-powered scheduling recommendations.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>3. User Accounts</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  You must create an account to use GraftAI. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>4. Acceptable Use</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  You agree to use GraftAI only for lawful purposes and in accordance with these Terms. You agree not to:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>Use the service for any illegal purpose</li>
                  <li>Attempt to gain unauthorized access to our systems</li>
                  <li>Interfere with or disrupt the service</li>
                  <li>Harvest or collect user information without consent</li>
                  <li>Upload malicious code or content</li>
                </Box>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>5. Subscription and Payments</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  Some features of GraftAI require a paid subscription. By subscribing, you agree to pay all fees associated with your subscription plan. Subscription fees are billed in advance and are non-refundable except as required by law.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>6. Data Privacy</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  Your privacy is important to us. Please review our <Link href="/privacy" style={{ color: '#6366f1' }}>Privacy Policy</Link> to understand how we collect, use, and protect your personal information and calendar data.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>7. Intellectual Property</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  GraftAI and its original content, features, and functionality are owned by GraftAI Inc. and are protected by international copyright, trademark, and other intellectual property laws.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>8. Limitation of Liability</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  In no event shall GraftAI be liable for any indirect, incidental, special, consequential, or punitive damages arising out of or related to your use of the service. Our total liability shall not exceed the amount you paid for the service in the past 12 months.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>9. Changes to Terms</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We may update these Terms from time to time. We will notify you of any material changes by posting the new Terms on this page and updating the "Last updated" date.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>10. Contact Information</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  If you have any questions about these Terms, please contact us at support@graftai.com or through our <Link href="/contact" style={{ color: '#6366f1' }}>contact page</Link>.
                </Typography>
              </Box>
            </Box>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
