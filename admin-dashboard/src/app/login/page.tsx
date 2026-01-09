"use client";

import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <div className="login-bg min-h-screen flex items-center justify-center p-4">
      {/* Decorative elements */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-[var(--jvc-red)]/5 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-[var(--jvc-red)]/3 rounded-full blur-3xl" />

      {/* Login Card */}
      <div className="glass relative z-10 w-full max-w-md rounded-2xl shadow-2xl p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl jvc-gradient mb-4">
            <span className="text-white font-bold text-2xl">JVC</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--jvc-black)]">
            AI Support Admin
          </h1>
          <p className="text-muted-foreground mt-2">
            Sign in to access the dashboard
          </p>
        </div>

        {/* Google Sign In Button */}
        <Button
          onClick={() => signIn("google", { callbackUrl: "/admin/bots" })}
          className="w-full h-12 bg-[var(--jvc-black)] hover:bg-[var(--jvc-black)]/90 text-white font-medium rounded-lg flex items-center justify-center gap-3 transition-all duration-200 hover:shadow-lg"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
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
        <p className="text-center text-sm text-muted-foreground mt-8">
          Only authorized JVC employees can access this dashboard
        </p>
      </div>

      {/* Floating glass elements for depth */}
      <div className="absolute top-1/4 right-1/4 w-20 h-20 glass rounded-2xl opacity-50 rotate-12" />
      <div className="absolute bottom-1/3 left-1/3 w-16 h-16 glass rounded-xl opacity-40 -rotate-6" />
    </div>
  );
}
