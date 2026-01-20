import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  trustHost: true,
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google" && user.email) {
        try {
          // Register/update user in backend
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://session-api-687023036300.us-central1.run.app";
          await fetch(`${apiUrl}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: user.email,
              name: user.name,
              avatar_url: user.image,
              google_id: account.providerAccountId,
            }),
          });
        } catch (error) {
          console.error("Failed to sync user with backend:", error);
        }
      }
      return true;
    },
    async jwt({ token, user, account, trigger }) {
      if (user) {
        token.id = user.id;
      }
      
      // Periodically refresh user status from backend or on initial sign in
      if (account || trigger === "signIn" || trigger === "update") {
        try {
          const email = token.email;
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://session-api-687023036300.us-central1.run.app";
          const res = await fetch(`${apiUrl}/auth/me?email=${email}`);
          if (res.ok) {
            const userData = await res.json();
            token.role = userData.role;
            token.is_approved = userData.is_approved;
          }
        } catch (error) {
          console.error("Failed to fetch user approval status:", error);
        }
      }
      
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
        session.user.is_approved = token.is_approved as boolean;
      }
      return session;
    },
  },
});
