'use client';

import { Box, Container, Typography, Paper } from '@mui/material';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function PrivacyPage() {
  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)', pt: 8, pb: 8 }}>
      <Container maxWidth="md">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Paper sx={{ p: { xs: 3, md: 6 }, background: 'linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 26, 0.98) 100%)', backdropFilter: 'blur(20px)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 4, background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Privacy Policy
            </Typography>
            
            <Typography variant="body2" sx={{ color: '#64748b', mb: 4 }}>
              Last updated: December 2024
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>1. Introduction</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  At GraftAI, we take your privacy seriously. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered scheduling platform. Please read this policy carefully to understand our practices regarding your data.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>2. Information We Collect</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We collect information that you provide directly to us, including:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>Account information (name, email, password)</li>
                  <li>Calendar data and event details</li>
                  <li>Meeting preferences and scheduling patterns</li>
                  <li>Usage data and analytics</li>
                  <li>Device and connection information</li>
                </Box>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>3. How We Use Your Information</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We use your information to:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>Provide and maintain our scheduling services</li>
                  <li>Train and improve our AI scheduling algorithms</li>
                  <li>Send notifications and reminders</li>
                  <li>Respond to your requests and support inquiries</li>
                  <li>Prevent fraud and ensure security</li>
                </Box>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>4. Calendar Data Processing</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  GraftAI requires access to your calendar data to provide scheduling services. We use this data solely for:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>Analyzing your availability patterns</li>
                  <li>Suggesting optimal meeting times</li>
                  <li>Automatically scheduling events based on your preferences</li>
                  <li>Sending meeting reminders and notifications</li>
                </Box>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7, mt: 1 }}>
                  We do not sell your calendar data to third parties or use it for advertising purposes.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>5. Data Security</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We implement industry-standard security measures to protect your data, including:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>AES-256 encryption for data at rest</li>
                  <li>TLS 1.3 for data in transit</li>
                  <li>Regular security audits and penetration testing</li>
                  <li>SOC 2 Type II certified infrastructure</li>
                  <li>Strict access controls and monitoring</li>
                </Box>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>6. Data Retention</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We retain your data for as long as your account is active or as needed to provide our services. You can request deletion of your data at any time by contacting us or using the account deletion feature in your settings.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>7. Your Rights</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  Depending on your location, you may have the right to:
                </Typography>
                <Box component="ul" sx={{ pl: 3, color: '#94a3b8', lineHeight: 1.8 }}>
                  <li>Access your personal data</li>
                  <li>Correct inaccurate data</li>
                  <li>Delete your data (right to be forgotten)</li>
                  <li>Export your data</li>
                  <li>Object to processing</li>
                  <li>Withdraw consent</li>
                </Box>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>8. Third-Party Services</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We integrate with third-party calendar providers (Google Calendar, Outlook, etc.) to sync your events. Their use of your data is governed by their respective privacy policies. We only access the minimum data necessary to provide our services.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>9. Children's Privacy</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  GraftAI is not intended for children under 13. We do not knowingly collect data from children under 13. If you believe we have collected data from a child under 13, please contact us immediately.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>10. Changes to This Policy</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  We may update this Privacy Policy periodically. We will notify you of significant changes via email or through our service. Continued use of GraftAI after changes constitutes acceptance of the updated policy.
                </Typography>
              </Box>

              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>11. Contact Us</Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.7 }}>
                  If you have questions about this Privacy Policy or our data practices, please contact us at:
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', mt: 1 }}>
                  Email: privacy@graftai.com<br />
                  Address: GraftAI Inc., 123 Tech Street, San Francisco, CA 94105<br />
                  <Link href="/contact" style={{ color: '#6366f1' }}>Contact Form</Link>
                </Typography>
              </Box>
            </Box>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
