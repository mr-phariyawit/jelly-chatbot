"use client";

import { useSession, signOut } from "next-auth/react";
import { LogOut, Loader2, Hourglass } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function PendingApprovalPage() {
  const { data: session } = useSession();

  const user = session?.user;
  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : user?.email?.[0].toUpperCase() || "U";

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-[#1a1a1a] border-yellow-500/20 shadow-2xl overflow-hidden">
        <CardContent className="pt-10 pb-8 px-8 flex flex-col items-center text-center">
          {/* Avatar Area */}
          <div className="relative mb-6">
            <div className="h-24 w-24 rounded-full border-2 border-yellow-500/50 flex items-center justify-center bg-yellow-500/5 text-3xl font-bold text-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.2)]">
              {initials}
            </div>
          </div>

          {/* User Email */}
          <h2 className="text-xl font-semibold text-white mb-4">
            {user?.email}
          </h2>

          {/* Status Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-500 text-sm font-medium mb-6">
            <Hourglass className="h-4 w-4 animate-spin-slow" />
            Pending Approval
          </div>

          {/* Message */}
          <p className="text-muted-foreground mb-8 leading-relaxed">
            Your account is awaiting admin approval. <br />
            We&apos;ll notify you when it&apos;s ready.
          </p>

          {/* Animated Loader (Bouncing dots) */}
          <div className="flex gap-2 mb-10">
            <div className="h-2 w-2 rounded-full bg-yellow-500 animate-bounce [animation-delay:-0.3s]" />
            <div className="h-2 w-2 rounded-full bg-yellow-500 animate-bounce [animation-delay:-0.15s]" />
            <div className="h-2 w-2 rounded-full bg-yellow-500 animate-bounce" />
          </div>

          {/* Logout Button */}
          <Button
            variant="ghost"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="text-muted-foreground hover:text-white hover:bg-white/5 transition-colors gap-2"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </CardContent>
      </Card>
      
      <style jsx global>{`
        @keyframes stripes {
          from { background-position: 0 0; }
          to { background-position: 1rem 0; }
        }
        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
