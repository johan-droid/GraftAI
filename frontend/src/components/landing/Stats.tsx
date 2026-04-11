"use client";

import { Box, Typography, Container, Grid } from "@mui/material";
import { motion } from "framer-motion";
import { Users, Calendar, Clock, Activity } from "lucide-react";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";

const stats = [
  {
    icon: Users,
    value: 50000,
    suffix: "+",
    label: "Active Users",
    color: "#6366f1",
  },
  {
    icon: Calendar,
    value: 1000000,
    suffix: "+",
    label: "Meetings Booked",
    color: "#ec4899",
  },
  {
    icon: Clock,
    value: 2500000,
    suffix: "+",
    label: "Hours Saved",
    color: "#10b981",
  },
  {
    icon: Activity,
    value: 99.9,
    suffix: "%",
    label: "Uptime SLA",
    color: "#f59e0b",
  },
];

export function Stats() {
  return (
    <Box
      sx={{
        py: { xs: 10, md: 16 },
        background: "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background Pattern */}
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          opacity: 0.3,
          backgroundImage: `radial-gradient(circle at 2px 2px, rgba(99, 102, 241, 0.15) 1px, transparent 0)`,
          backgroundSize: "40px 40px",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1 }}>
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
              Trusted by{" "}
              <Box
                component="span"
                sx={{
                  background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Thousands
              </Box>
            </Typography>
          </motion.div>
        </Box>

        {/* Stats Grid */}
        <Grid container spacing={3}>
          {stats.map((stat, index) => (
            <Grid item xs={6} md={3} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Box
                  sx={{
                    textAlign: "center",
                    p: { xs: 3, md: 4 },
                    background: "rgba(15, 15, 26, 0.5)",
                    borderRadius: 3,
                    border: "1px solid rgba(99, 102, 241, 0.1)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: `${stat.color}50`,
                      boxShadow: `0 20px 40px -20px ${stat.color}30`,
                    },
                  }}
                >
                  <Box
                    sx={{
                      width: 56,
                      height: 56,
                      borderRadius: 2,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: `${stat.color}20`,
                      mx: "auto",
                      mb: 2,
                    }}
                  >
                    <stat.icon size={28} style={{ color: stat.color }} />
                  </Box>
                  <AnimatedCounter
                    end={stat.value}
                    suffix={stat.suffix}
                    variant="h3"
                    sx={{
                      fontSize: { xs: "2rem", md: "2.5rem" },
                      mb: 1,
                    }}
                  />
                  <Typography variant="body1" sx={{ color: "#94a3b8" }}>
                    {stat.label}
                  </Typography>
                </Box>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
