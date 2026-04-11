"use client";

import { Box, Typography, Container, Grid, Paper, Avatar, Rating } from "@mui/material";
import { motion } from "framer-motion";
import { Quote, BadgeCheck } from "lucide-react";

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Product Manager",
    company: "TechCorp",
    avatar: "SC",
    rating: 5,
    quote: "GraftAI has completely transformed how our team schedules meetings. The AI suggestions are incredibly accurate—it feels like having a personal assistant.",
    featured: true,
  },
  {
    name: "Michael Roberts",
    role: "CEO",
    company: "StartupXYZ",
    avatar: "MR",
    rating: 5,
    quote: "I save at least 5 hours every week on scheduling. The ROI has been phenomenal for our organization. Best investment we've made.",
    featured: false,
  },
  {
    name: "Emily Watson",
    role: "Engineering Lead",
    company: "DevCo",
    avatar: "EW",
    rating: 5,
    quote: "The calendar sync across Google, Outlook, and Apple is seamless. Finally, a scheduling tool that just works across all platforms.",
    featured: false,
  },
  {
    name: "David Kim",
    role: "Sales Director",
    company: "CloudScale",
    avatar: "DK",
    rating: 5,
    quote: "My team's meeting coordination improved by 80%. No more back-and-forth emails trying to find a time that works for everyone.",
    featured: false,
  },
  {
    name: "Lisa Park",
    role: "Operations Manager",
    company: "FlowTech",
    avatar: "LP",
    rating: 5,
    quote: "The focus time protection feature is a game-changer. I finally have uninterrupted blocks for deep work.",
    featured: false,
  },
  {
    name: "James Wilson",
    role: "CTO",
    company: "DataDriven",
    avatar: "JW",
    rating: 5,
    quote: "As someone who lives in their calendar, GraftAI is the first tool that actually understands my workflow. Highly recommend!",
    featured: false,
  },
];

export function Testimonials() {
  const featured = testimonials.find((t) => t.featured);
  const regular = testimonials.filter((t) => !t.featured);

  return (
    <Box id="testimonials" sx={{ py: { xs: 10, md: 16 } }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Box sx={{ textAlign: "center", mb: { xs: 6, md: 10 } }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <Typography
              variant="h2"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.25rem", md: "3rem" }, fontWeight: 800, mb: 2 }}
            >
              Loved by{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Teams Worldwide
              </Box>
            </Typography>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <Typography variant="body1" sx={{ color: "#94a3b8", maxWidth: 600, mx: "auto" }}>
              See what professionals are saying about GraftAI
            </Typography>
          </motion.div>
        </Box>

        {/* Featured Testimonial */}
        {featured && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            style={{ marginBottom: 48 }}
          >
            <Paper
              sx={{
                p: { xs: 4, md: 6 },
                background: "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%)",
                border: "1px solid rgba(99, 102, 241, 0.2)",
                borderRadius: 3,
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Quote Icon */}
              <Box
                sx={{
                  position: "absolute",
                  top: 20,
                  right: 20,
                  opacity: 0.1,
                }}
              >
                <Quote size={80} style={{ color: "#6366f1" }} />
              </Box>

              <Box sx={{ position: "relative", zIndex: 1 }}>
                <Rating value={featured.rating} readOnly sx={{ mb: 2 }} />
                <Typography
                  variant="h5"
                  sx={{
                    fontStyle: "italic",
                    color: "#f8fafc",
                    mb: 4,
                    fontSize: { xs: "1.1rem", md: "1.5rem" },
                    lineHeight: 1.6,
                  }}
                >
                  "{featured.quote}"
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                  <Avatar
                    sx={{
                      width: 56,
                      height: 56,
                      background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                      fontWeight: 600,
                    }}
                  >
                    {featured.avatar}
                  </Avatar>
                  <Box>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        {featured.name}
                      </Typography>
                      <BadgeCheck size={16} style={{ color: "#6366f1" }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: "#94a3b8" }}>
                      {featured.role} at {featured.company}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Paper>
          </motion.div>
        )}

        {/* Testimonial Grid */}
        <Grid container spacing={3}>
          {regular.map((testimonial, index) => (
            <Grid item xs={12} sm={6} lg={4} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                style={{ height: "100%" }}
              >
                <Paper
                  sx={{
                    height: "100%",
                    p: 3,
                    background: "linear-gradient(135deg, rgba(26, 26, 46, 0.8) 0%, rgba(15, 15, 26, 0.9) 100%)",
                    border: "1px solid rgba(99, 102, 241, 0.1)",
                    borderRadius: 3,
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: "rgba(99, 102, 241, 0.3)",
                      transform: "translateY(-4px)",
                      boxShadow: "0 20px 40px -20px rgba(99, 102, 241, 0.2)",
                    },
                  }}
                >
                  <Rating value={testimonial.rating} readOnly size="small" sx={{ mb: 2 }} />
                  <Typography
                    variant="body1"
                    sx={{
                      color: "#e2e8f0",
                      mb: 3,
                      fontStyle: "italic",
                      lineHeight: 1.6,
                    }}
                  >
                    "{testimonial.quote}"
                  </Typography>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <Avatar
                      sx={{
                        width: 44,
                        height: 44,
                        background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                        fontSize: "0.875rem",
                        fontWeight: 600,
                      }}
                    >
                      {testimonial.avatar}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {testimonial.name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: "#64748b" }}>
                        {testimonial.role}, {testimonial.company}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
