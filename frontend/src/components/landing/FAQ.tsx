"use client";

import { useState } from "react";
import { Box, Typography, Container, Paper } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, HelpCircle } from "lucide-react";

const faqs = [
  {
    question: "How does the AI scheduling work?",
    answer:
      "GraftAI uses machine learning to understand your scheduling patterns, preferences, and work habits. It analyzes your calendar history, learns when you prefer meetings, and automatically suggests optimal times while protecting your focus blocks. The AI improves with every interaction.",
  },
  {
    question: "Which calendars do you support?",
    answer:
      "We support all major calendar platforms including Google Calendar, Microsoft Outlook/Exchange, Apple iCloud Calendar, and any CalDAV-compatible service. You can connect multiple calendars and we'll sync them all in real-time.",
  },
  {
    question: "Is my data secure?",
    answer:
      "Absolutely. We use bank-level AES-256 encryption for all data at rest and in transit. We're SOC 2 Type II certified, GDPR compliant, and never sell your data. Your calendar information is only used to provide scheduling services.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "Yes! You can cancel your subscription at any time with no questions asked. If you cancel, you'll continue to have access until the end of your billing period. We also offer a 30-day money-back guarantee for paid plans.",
  },
  {
    question: "What's included in the free plan?",
    answer:
      "The free plan includes up to 100 scheduled events per month, basic AI assistance, email notifications, mobile app access, and Google Calendar sync. It's perfect for individuals who need simple scheduling help.",
  },
  {
    question: "Do you offer team plans?",
    answer:
      "Yes! Our Pro plan supports teams up to 5 members, and Enterprise supports unlimited team members with advanced collaboration features, admin controls, and SSO integration. Contact us for team pricing.",
  },
  {
    question: "How do I get started?",
    answer:
      "Simply sign up for a free account, connect your calendar(s), and start scheduling. Our onboarding wizard will guide you through setting your preferences. Most users are up and running within 2 minutes.",
  },
  {
    question: "Do you have an API?",
    answer:
      "Yes, we offer a comprehensive REST API for Enterprise customers. You can programmatically create events, manage users, access analytics, and integrate GraftAI into your own applications. Check our developer documentation for details.",
  },
];

function FAQItem({ question, answer, isOpen, onClick }: { question: string; answer: string; isOpen: boolean; onClick: () => void }) {
  return (
    <Paper
      onClick={onClick}
      sx={{
        mb: 2,
        background: "rgba(26, 26, 46, 0.5)",
        border: "1px solid rgba(99, 102, 241, 0.1)",
        borderRadius: 2,
        overflow: "hidden",
        cursor: "pointer",
        transition: "all 0.3s ease",
        "&:hover": {
          borderColor: "rgba(99, 102, 241, 0.3)",
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, fontSize: "1rem" }}>
            {question}
          </Typography>
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown size={20} style={{ color: "#94a3b8" }} />
          </motion.div>
        </Box>
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Box sx={{ pt: 2, borderTop: "1px solid rgba(99, 102, 241, 0.1)", mt: 2 }}>
                <Typography variant="body1" sx={{ color: "#94a3b8", lineHeight: 1.7 }}>
                  {answer}
                </Typography>
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>
    </Paper>
  );
}

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <Box sx={{ py: { xs: 10, md: 16 }, background: "rgba(26, 26, 46, 0.3)" }}>
      <Container maxWidth="md">
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 8 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: 2,
                background: "rgba(99, 102, 241, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                mx: "auto",
                mb: 3,
              }}
            >
              <HelpCircle size={28} style={{ color: "#6366f1" }} />
            </Box>
            <Typography
              variant="h2"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Frequently Asked{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Questions
              </Box>
            </Typography>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Typography variant="body1" sx={{ color: "#94a3b8" }}>
              Everything you need to know about GraftAI
            </Typography>
          </motion.div>
        </Box>

        {/* FAQ Items */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          viewport={{ once: true }}
        >
          {faqs.map((faq, index) => (
            <FAQItem
              key={index}
              question={faq.question}
              answer={faq.answer}
              isOpen={openIndex === index}
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
            />
          ))}
        </motion.div>

        {/* Contact CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          viewport={{ once: true }}
        >
          <Box sx={{ textAlign: "center", mt: 6 }}>
            <Typography variant="body1" sx={{ color: "#94a3b8" }}>
              Still have questions?{" "}
              <Box
                component="a"
                href="/contact"
                sx={{
                  color: "#6366f1",
                  textDecoration: "none",
                  fontWeight: 600,
                  "&:hover": { textDecoration: "underline" },
                }}
              >
                Contact our support team
              </Box>
            </Typography>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}
