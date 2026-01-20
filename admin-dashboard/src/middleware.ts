import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnLoginPage = req.nextUrl.pathname === "/login";
  const isOnAdminPage = req.nextUrl.pathname.startsWith("/admin");
  const isApiRoute = req.nextUrl.pathname.startsWith("/api");
  const isPendingPage = req.nextUrl.pathname === "/pending-approval";

  // Allow API routes
  if (isApiRoute) {
    return NextResponse.next();
  }

  // Handle Approval Status
  // Explicit whitelist bypass for superadmin to ensure they never get stuck
  const isSuperAdminEmail = req.auth?.user?.email === "mr.phariyawit@gmail.com";
  
  if (isLoggedIn && !req.auth?.user?.is_approved && !isPendingPage && !isSuperAdminEmail) {
    // If not approved and not on the pending page, send them there
    return NextResponse.redirect(new URL("/pending-approval", req.url));
  }

  if (isLoggedIn && (req.auth?.user?.is_approved || isSuperAdminEmail) && isPendingPage) {
    // If approved (or superadmin) but on pending page, send to dashboard
    return NextResponse.redirect(new URL("/admin/bots", req.url));
  }

  // Redirect logged-in users away from login page
  if (isLoggedIn && isOnLoginPage) {
    return NextResponse.redirect(new URL("/admin/bots", req.url));
  }

  // Protect admin routes
  if (!isLoggedIn && isOnAdminPage) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Redirect root to admin/bots if logged in, login if not
  if (req.nextUrl.pathname === "/") {
    if (isLoggedIn) {
      if (!req.auth?.user?.is_approved) {
        return NextResponse.redirect(new URL("/pending-approval", req.url));
      }
      return NextResponse.redirect(new URL("/admin/bots", req.url));
    }
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
