import type { Metadata } from "next";
import { JetBrains_Mono, Outfit, Permanent_Marker, Plus_Jakarta_Sans } from "next/font/google";
import { SessionProvider } from "next-auth/react";
import { AuthProvider } from "./providers/auth-provider";
import { QueryProvider } from "./providers/query-provider";
import { ThemeProvider } from "@/contexts/ThemeContext";
import ThemeRegistry from "@/theme/ThemeRegistry";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "700", "800"],
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["300", "400", "500", "600", "700"],
});

const permanentMarker = Permanent_Marker({
  subsets: ["latin"],
  variable: "--font-handwriting",
  weight: "400",
});

export const metadata: Metadata = {
  title: "GraftAI | Intelligent Scheduling",
  description: "Scheduling, simplified by AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${plusJakartaSans.variable} ${jetBrainsMono.variable} ${outfit.variable} ${permanentMarker.variable} min-h-dvh overflow-x-hidden font-sans antialiased text-[#202124] bg-[#F8F9FA]`}
      >
        <SessionProvider>
          <AuthProvider>
            <QueryProvider>
              <ThemeProvider>
                <ThemeRegistry>
                  {children}
                  {/* Global Toast Notifications */}
                  <Toaster
                    position="bottom-right"
                    toastOptions={{
                      style: {
                        background: '#333',
                        color: '#fff',
                        borderRadius: '100px',
                        fontSize: '14px',
                      },
                    }}
                  />
                </ThemeRegistry>
              </ThemeProvider>
            </QueryProvider>
          </AuthProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
