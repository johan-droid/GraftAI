"use client";

import { Box } from "@mui/material";
import { Navigation } from "@/components/landing/Navigation";
import { Hero } from "@/components/landing/Hero";
import { LogoCloud } from "@/components/landing/LogoCloud";
import { ProblemSolution } from "@/components/landing/ProblemSolution";
import { ProductShowcase } from "@/components/landing/ProductShowcase";
import { IntegrationShowcase } from "@/components/landing/IntegrationShowcase";
import { Comparison } from "@/components/landing/Comparison";
import { FeatureBento } from "@/components/landing/FeatureBento";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Testimonials } from "@/components/landing/Testimonials";
import { Stats } from "@/components/landing/Stats";
import { Pricing } from "@/components/landing/Pricing";
import { FAQ } from "@/components/landing/FAQ";
import { CTASection } from "@/components/landing/CTASection";
import { Newsletter } from "@/components/landing/Newsletter";
import { Footer } from "@/components/landing/Footer";
import { ScrollProgress } from "@/components/landing/ScrollProgress";
import { BackToTop } from "@/components/landing/BackToTop";
import { FloatingOrbs } from "@/components/landing/FloatingOrbs";
import { CookieConsent } from "@/components/landing/CookieConsent";

export default function Home() {
  return (
    <Box 
      sx={{ 
        minHeight: "100vh", 
        background: "var(--bg)", 
        position: "relative",
        // The grid and scanlines are in body::before/after in globals.css
      }}
    >
      {/* Visual Infrastructure */}
      <FloatingOrbs />
      <ScrollProgress />

      {/* Primary Navigation Layer */}
      <Navigation />

      {/* Main Content Stream */}
      <Box sx={{ position: "relative", zIndex: 1 }}>
        <Hero />
        <LogoCloud />
        
        {/* We keep these but the global typography/theme handles the coder look */}
        <Box sx={{ borderBottom: "1px solid var(--border-dotted)" }}>
          <IntegrationShowcase />
        </Box>
        
        <FeatureBento />
        
        <Box sx={{ borderTop: "1px solid var(--border-dotted)", background: "rgba(0,0,0,0.1)" }}>
          <ProductShowcase />
        </Box>

        <ProblemSolution />
        <Comparison />
        <HowItWorks />
        
        <Box sx={{ borderTop: "1px solid var(--border-dotted)" }}>
          <Pricing />
        </Box>

        <Testimonials />
        <Stats />
        <CTASection variant="email" />
        <FAQ />
        <CTASection variant="buttons" />
        <Newsletter />
        <Footer />
      </Box>

      {/* Peripheral UI */}
      <BackToTop />
      <CookieConsent />
    </Box>
  );
}
