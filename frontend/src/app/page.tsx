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
import { GrainOverlay } from "@/components/landing/GrainOverlay";
import { FloatingOrbs } from "@/components/landing/FloatingOrbs";
import { CookieConsent } from "@/components/landing/CookieConsent";
import DeveloperCorner from "@/components/DeveloperCorner";

export default function Home() {
  return (
    <Box sx={{ minHeight: "100vh", background: "#0f0f1a", position: "relative" }}>
      {/* Visual Effects */}
      <FloatingOrbs />
      <GrainOverlay />
      <ScrollProgress />

      {/* Navigation */}
      <Navigation />

      {/* Main Content */}
      <Box sx={{ position: "relative", zIndex: 1 }}>
        <Hero />
        <LogoCloud />
        <ProblemSolution />
        <IntegrationShowcase />
        <ProductShowcase />
        <FeatureBento />
        <Comparison />
        <HowItWorks />
        <Testimonials />
        <Stats />
        <Pricing />
        <CTASection variant="email" />
        <FAQ />
        <CTASection variant="buttons" />
        <Newsletter />
        <DeveloperCorner />
        <Footer />
      </Box>

      {/* Floating Elements */}
      <BackToTop />
      <CookieConsent />
    </Box>
  );
}
