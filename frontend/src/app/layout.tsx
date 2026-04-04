import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/app/providers/auth-provider";
import { Navbar } from "@/components/navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GraftAI Scheduler",
  description: "Next-Gen AI SaaS Scheduler with a dark galaxy aesthetic",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "GraftAI",
  },
  formatDetection: {
    telephone: false,
  },
  icons: [
    { rel: "icon", url: "/favicon.ico" },
    { rel: "icon", url: "/icon-192x192.png" },
    { rel: "apple-touch-icon", url: "/icon-192x192.png" },
  ],
  manifest: "/manifest.json",
};

export const viewport = {
  width: "device-width",
  initialScale: 1.0,
  minimumScale: 1.0,
  maximumScale: 1.0,
  userScalable: false,
};

export const themeColor = [
  { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
  { media: "(prefers-color-scheme: dark)", color: "#020617" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
      suppressHydrationWarning
      data-scroll-behavior="smooth"
    >
      <body className="min-h-full flex flex-col bg-background text-foreground selection:bg-primary/30" suppressHydrationWarning>
        <AuthProvider>
          <Navbar />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
