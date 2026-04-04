import type { Metadata, Viewport } from "next";
import { DM_Sans, DM_Serif_Display } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/app/providers/auth-provider";
import { NotificationProvider } from "@/providers/notification-provider";
import { ToastContainer } from "@/components/ui/Toast";

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
};

export const viewport: Viewport = {
  themeColor: "#070711",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${dmSerif.variable} dark`}
      suppressHydrationWarning
    >
      <body
        className="min-h-dvh bg-[#070711] text-slate-200 antialiased"
        style={{ fontFamily: "var(--font-dm-sans), system-ui, sans-serif" }}
        suppressHydrationWarning
      >
        <NotificationProvider>
          <AuthProvider>
            {children}
            <ToastContainer />
          </AuthProvider>
        </NotificationProvider>
      </body>
    </html>
  );
}
