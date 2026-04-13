"use client";

import { Box, Typography, Stack } from "@mui/material";
import { motion } from "framer-motion";
import { Copy, Terminal, Check } from "lucide-react";
import { useState } from "react";

const SNIPPETS = [
  {
    name: "Initialize Sync",
    lang: "typescript",
    code: `import { GraftAI } from '@graftai/node';

const client = new GraftAI({
  apiKey: process.env.GRAFT_API_KEY
});

// Sync calendar with AI Semantic Memory
await client.sync.calendar({
  userId: 'user_882',
  provider: 'google',
  options: { vectorize: true }
});`,
  },
  {
    name: "AI Suggestion",
    lang: "python",
    code: `from graftai import Client

client = Client(api_key="sk_live_...")

# Get AI-optimized meeting slot
suggestion = client.ai.suggest_slot(
    user_id="user_882",
    duration=30,
    context="Quarterly review with the DevOps team"
)

print(f"Optimal Slot: {suggestion.start_time}")`,
  }
];

export function CodeSnippetPreview() {
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(SNIPPETS[activeTab].code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: "600px",
        background: "#050505",
        borderRadius: "0",
        border: "1px dashed var(--border-subtle)",
        overflow: "hidden",
        boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          px: 2,
          py: 1.5,
          background: "rgba(255,255,255,0.02)",
          borderBottom: "1px dashed var(--border-subtle)",
        }}
      >
        <Stack direction="row" spacing={1} sx={{ mr: 4 }}>
          <Box sx={{ width: 6, height: 6, border: "1px solid var(--text-faint)", opacity: 0.3 }} />
          <Box sx={{ width: 6, height: 6, border: "1px solid var(--text-faint)", opacity: 0.6 }} />
          <Box sx={{ width: 6, height: 6, background: "var(--primary)" }} />
        </Stack>

        <Stack direction="row" spacing={4} sx={{ flex: 1 }}>
          {SNIPPETS.map((s, i) => (
            <Typography
              key={s.name}
              onClick={() => setActiveTab(i)}
              sx={{
                fontSize: "10px",
                fontWeight: 800,
                color: activeTab === i ? "var(--primary)" : "var(--text-faint)",
                cursor: "pointer",
                transition: "all 0.2s",
                "&:hover": { color: "var(--text-primary)" },
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                position: "relative",
                pb: 0.5,
                "&::after": activeTab === i ? {
                  content: '""',
                  position: "absolute",
                  bottom: -8,
                  left: 0,
                  right: 0,
                  height: 1,
                  background: "var(--primary)"
                } : {}
              }}
            >
              {s.name}
            </Typography>
          ))}
        </Stack>

        <Box 
          onClick={handleCopy} 
          sx={{ 
            cursor: "pointer", 
            color: "var(--text-faint)", 
            "&:hover": { color: "var(--primary)" },
            display: "flex",
            alignItems: "center",
            gap: 1
          }}
        >
          {copied ? (
            <>
              <span className="text-[8px] font-black text-[var(--primary)] font-mono">COPIED</span>
              <Check size={12} />
            </>
          ) : (
            <Copy size={12} />
          )}
        </Box>
      </Box>

      {/* Code Area */}
      <Box sx={{ p: { xs: 2.5, md: 4 }, position: "relative" }}>
        <pre style={{ margin: 0, overflowX: "auto" }}>
          <code style={{ 
            fontFamily: "var(--font-mono)", 
            fontSize: "12px", 
            color: "var(--text-secondary)", 
            lineHeight: 1.8,
            display: "block",
            whiteSpace: "pre"
          }}>
            {SNIPPETS[activeTab].code.split("\n").map((line, i) => (
              <div key={i} style={{ display: "flex" }}>
                <span style={{ 
                  width: "32px", 
                  color: "var(--text-faint)", 
                  userSelect: "none", 
                  flexShrink: 0,
                  textAlign: "right",
                  paddingRight: "20px",
                  fontSize: "10px",
                  opacity: 0.4
                }}>{(i + 1).toString().padStart(2, '0')}</span>
                <span style={{ color: "var(--text-primary)" }}>{line}</span>
              </div>
            ))}
          </code>
        </pre>

        {/* Floating Indicator */}
        <Box
          sx={{
            position: "absolute",
            bottom: 12,
            right: 12,
            display: "flex",
            alignItems: "center",
            gap: 1,
            color: "var(--primary)",
            opacity: 0.3,
            fontSize: "9px",
            fontFamily: "var(--font-mono)",
            fontWeight: 900,
            letterSpacing: "0.1em"
          }}
        >
          <Terminal size={10} />
          {SNIPPETS[activeTab].lang.toUpperCase()}_ENV
        </Box>
      </Box>
    </Box>
  );
}
