"use client";

import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[var(--bg-primary)] font-sans">
      
      {/* --- 1. The Aurora Blobs (Background Animation) --- */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        
        {/* Blob 1: Pink */}
        <div
          className="absolute -top-[10%] -left-[10%] w-[500px] h-[500px] rounded-full bg-[#FF8FAB] blur-[80px] opacity-70 animate-fluid-1 mix-blend-screen"
        />

        {/* Blob 2: Lavender */}
        <div
          className="absolute -bottom-[10%] -right-[10%] w-[400px] h-[400px] rounded-full bg-[#C8B3E0] blur-[80px] opacity-70 animate-fluid-2 mix-blend-screen"
          style={{ animationDelay: '-5s' }}
        />

        {/* Blob 3: Deep Lavender */}
        <div
          className="absolute bottom-[20%] left-[20%] w-[300px] h-[300px] rounded-full bg-[#B09BD9] blur-[80px] opacity-50 animate-fluid-3 mix-blend-screen"
          style={{ animationDelay: '-10s' }}
        />
      </div>

      {/* --- 2. Login Card (Original Theme) --- */}
      <div className="relative z-10 w-full max-w-md p-8 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] shadow-2xl">
        
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-24 h-24 mb-6 bg-[var(--pink-light)]/10 rounded-full border border-[var(--pink)]/20 p-4">
            <img
              src="/profile-jelly.png"
              alt="Jelly ChatBot Logo"
              className="object-contain w-full h-full rounded-full"
            />
          </div>
          <h1 className="text-3xl font-bold text-[var(--pink)] mb-3">
            Jelly ChatBot
          </h1>
          <p className="text-[var(--text-secondary)]">
            Sign in to manage Jelly ChatBot
          </p>
        </div>

        {/* Google Sign In Button (Jelly Theme) */}
        <Button
          onClick={() => signIn("google", { callbackUrl: "/admin/bots" })}
          className="w-full h-14 btn-pink-gradient font-semibold text-lg rounded-xl flex items-center justify-center gap-3"
        >
          <svg className="w-6 h-6" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Sign in with Google
        </Button>

        {/* Footer */}
        <p className="text-center text-sm text-[var(--text-secondary)] mt-8 opacity-60">
          Only authorized personnel can access this dashboard
        </p>
      </div>
    </div>
  );
}
