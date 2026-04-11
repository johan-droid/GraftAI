"use client";

import { Box, Typography, Container, Grid, Divider, IconButton } from "@mui/material";
import Link from "next/link";
import { 
  Sparkles,
  CheckCircle 
} from "lucide-react";

// Social icons as custom components since Lucide doesn't have them
const TwitterIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" />
  </svg>
);

const LinkedinIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const GithubIcon = ({ size = 20 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

const footerLinks = {
  product: {
    title: "Product",
    links: [
      { label: "Features", href: "#features" },
      { label: "Pricing", href: "#pricing" },
      { label: "Integrations", href: "/integrations" },
      { label: "API", href: "/developers" },
      { label: "Security", href: "/security" },
    ],
  },
  resources: {
    title: "Resources",
    links: [
      { label: "Documentation", href: "/docs" },
      { label: "Blog", href: "/blog" },
      { label: "Changelog", href: "/changelog" },
      { label: "Help Center", href: "/help" },
      { label: "Community", href: "/community" },
    ],
  },
  company: {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Careers", href: "/careers" },
      { label: "Press", href: "/press" },
      { label: "Contact", href: "/contact" },
      { label: "Partners", href: "/partners" },
    ],
  },
  legal: {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
      { label: "GDPR", href: "/gdpr" },
      { label: "Cookies", href: "/cookies" },
    ],
  },
};

const socialLinks = [
  { icon: TwitterIcon, href: "https://twitter.com/graftai", label: "Twitter" },
  { icon: LinkedinIcon, href: "https://linkedin.com/company/graftai", label: "LinkedIn" },
  { icon: GithubIcon, href: "https://github.com/graftai", label: "GitHub" },
];

export function Footer() {
  return (
    <Box sx={{ background: "rgba(15, 15, 26, 0.95)", borderTop: "1px solid rgba(99, 102, 241, 0.1)" }}>
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 } }}>
        <Grid container spacing={6}>
          {/* Brand Column */}
          <Grid item xs={12} md={4}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
              <Sparkles size={28} style={{ color: "#6366f1" }} />
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                GraftAI
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ color: "#64748b", mb: 3, maxWidth: 280 }}>
              AI-powered scheduling platform that transforms how you manage your time
              and meetings. Built for modern professionals.
            </Typography>

            {/* Social Links */}
            <Box sx={{ display: "flex", gap: 1 }}>
              {socialLinks.map((social) => (
                <IconButton
                  key={social.label}
                  component={Link}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    color: "#64748b",
                    "&:hover": {
                      color: "#6366f1",
                      background: "rgba(99, 102, 241, 0.1)",
                    },
                  }}
                >
                  <social.icon size={20} />
                </IconButton>
              ))}
            </Box>
          </Grid>

          {/* Link Columns */}
          {Object.entries(footerLinks).map(([key, section]) => (
            <Grid item xs={6} sm={6} md={2} key={key}>
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  mb: 2,
                  color: "#f8fafc",
                  fontSize: "0.875rem",
                }}
              >
                {section.title}
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                {section.links.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    style={{
                      color: "#64748b",
                      textDecoration: "none",
                      fontSize: "0.875rem",
                      transition: "color 0.2s",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = "#a5b4fc";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = "#64748b";
                    }}
                  >
                    {link.label}
                  </Link>
                ))}
              </Box>
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ my: 6, borderColor: "rgba(99, 102, 241, 0.1)" }} />

        {/* Bottom Bar */}
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Typography variant="body2" sx={{ color: "#475569" }}>
            © 2024 GraftAI. All rights reserved.
          </Typography>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CheckCircle size={14} style={{ color: "#10b981" }} />
            <Typography variant="body2" sx={{ color: "#475569" }}>
              All systems operational
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}
