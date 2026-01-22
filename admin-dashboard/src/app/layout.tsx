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
  title: "Jelly ChatBot",
  description: "Admin dashboard for Jelly ChatBot",
  icons: {
    icon: '/profile-jelly.png',
    shortcut: '/profile-jelly.png',
    apple: '/profile-jelly.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
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
