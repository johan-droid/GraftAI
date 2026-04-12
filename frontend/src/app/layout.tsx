import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/app/providers/auth-provider";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "@/components/ui/Toast";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "GraftAI", template: "%s — GraftAI" },
  description: "AI-powered scheduling and calendar orchestration for modern teams.",
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "https://graftai.com"),
  openGraph: {
    type: "website",
    title: "GraftAI",
    description: "AI-powered scheduling and calendar orchestration.",
    siteName: "GraftAI",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: dark)",  color: "#0A0A0B" },
    { media: "(prefers-color-scheme: light)", color: "#F9F5F2" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  return (
    <html
      lang="en"
      className={`${jakarta.variable} h-full`}
      suppressHydrationWarning
    >
      <head>
        {/* Preconnect to backend */}
        {apiBase && <link rel="preconnect" href={apiBase} />}
      </head>
      <body
        className="min-h-full flex flex-col"
        style={{ background: "var(--bg)", color: "var(--text)", fontFamily: "var(--font-jakarta), ui-sans-serif, system-ui, sans-serif" }}
        suppressHydrationWarning
      >
        <AuthProvider>
          <ThemeProvider>
            {children}
            <Toaster />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
