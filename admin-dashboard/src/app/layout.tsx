import type { Metadata } from "next";
import { Prompt, IBM_Plex_Sans, Geist_Mono } from "next/font/google";
import "./globals.css";

import Providers from "@/components/providers";
import { AuthProvider } from "@/components/auth-provider";

const prompt = Prompt({
  weight: ["300", "400", "500", "600", "700"],
  subsets: ["thai", "latin"],
  variable: "--font-prompt",
});

const ibmPlexSans = IBM_Plex_Sans({
    weight: ["400", "500", "600", "700"],
    subsets: ["latin"],
    variable: "--font-ibm-plex",
  });

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Support Platform",
  description: "Admin dashboard for AI Support Platform",
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
    apple: '/logo.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${prompt.variable} ${ibmPlexSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <AuthProvider>
          <Providers>{children}</Providers>
        </AuthProvider>
      </body>
    </html>
  );
}
