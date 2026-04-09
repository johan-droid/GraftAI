import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GraftAI UI Shell",
  description: "A minimal frontend shell for GraftAI UI development.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
