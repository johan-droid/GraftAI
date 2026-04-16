import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SessionProvider } from "next-auth/react";
import { AuthProvider } from "./providers/auth-provider";
import { QueryProvider } from "./providers/query-provider";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

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
      <body className={`${inter.variable} font-sans antialiased text-[#202124] bg-[#F8F9FA]`}>
        <SessionProvider>
          <AuthProvider>
            <QueryProvider>
              <ThemeProvider>
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
              </ThemeProvider>
            </QueryProvider>
          </AuthProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
