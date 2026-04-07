import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import { DM_Sans, DM_Serif_Display } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/app/providers/auth-provider";
import { NotificationProvider } from "@/providers/notification-provider";
import { Toaster } from "sonner";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
});

const dmSerif = DM_Serif_Display({
  variable: "--font-dm-serif",
  subsets: ["latin"],
  weight: ["400"],
  display: "swap",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: {
    default: "GraftAI — Scheduling, handled.",
    template: "%s · GraftAI",
  },
  description:
    "AI-powered scheduling that handles timezones, conflicts, and back-and-forth — so you just show up.",
  keywords: ["scheduling", "AI", "calendar", "meetings", "productivity"],
  authors: [{ name: "GraftAI" }],
  openGraph: {
    type: "website",
    title: "GraftAI — Scheduling, handled.",
    description: "AI-powered scheduling that handles timezones, conflicts, and back-and-forth.",
    siteName: "GraftAI",
  },
  twitter: {
    card: "summary_large_image",
    title: "GraftAI — Scheduling, handled.",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "GraftAI",
  },
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f6fc" },
    { media: "(prefers-color-scheme: dark)", color: "#070711" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  maximumScale: 1,
  userScalable: false,
  interactiveWidget: "resizes-content",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const nonce = (await headers()).get("x-nonce") || "";

  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${dmSerif.variable}`}
      suppressHydrationWarning
      data-scroll-behavior="smooth"
    >
      <body
        className="min-h-dvh antialiased"
        suppressHydrationWarning
      >
        <NotificationProvider>
          <AuthProvider>
            {children}
            <Toaster position="top-right" expand={false} richColors closeButton theme="dark" />
          </AuthProvider>
        </NotificationProvider>
      </body>
    </html>
  );
}
