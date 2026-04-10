import type { Metadata, Viewport } from "next";
import "./globals.css";
import ThemeRegistry from "@/theme/ThemeRegistry";
import { AuthProvider } from "@/providers/auth-provider";

export const metadata: Metadata = {
  title: "GraftAI - AI-Powered Scheduling Platform",
  description: "GraftAI intelligently manages your calendar, schedules meetings, and optimizes your time with AI-powered automation.",
  keywords: ["AI scheduling", "calendar automation", "meeting scheduler", "productivity", "time management"],
  authors: [{ name: "GraftAI Team" }],
  openGraph: {
    title: "GraftAI - AI-Powered Scheduling Platform",
    description: "Intelligent calendar management and meeting automation powered by AI",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f0f1a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <ThemeRegistry>
          <AuthProvider>
            {children}
          </AuthProvider>
        </ThemeRegistry>
      </body>
    </html>
  );
}
