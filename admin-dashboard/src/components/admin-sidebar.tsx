'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { LayoutDashboard, MessageSquare, Bot, LogOut, ChevronDown, Settings, PanelLeftClose, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ApiStatusIndicator } from '@/components/api-status-indicator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export function AdminSidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  // Load collapsed state from localStorage using lazy initial state
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false;
    const saved = localStorage.getItem('sidebar-collapsed');
    return saved !== null ? JSON.parse(saved) : false;
  });

  // Save collapsed state to localStorage
  const toggleCollapsed = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('sidebar-collapsed', JSON.stringify(newState));
  };

  const links = [
    {
      href: '/admin/bots',
      label: 'Bots',
      icon: Bot,
    },
    {
      href: '/admin/sessions',
      label: 'Sessions',
      icon: MessageSquare,
    },
    {
        href: '/admin/analytics',
        label: 'Analytics',
        icon: LayoutDashboard,
    },
    {
        href: '/admin/settings',
        label: 'Settings',
        icon: Settings,
    }
  ];

  const getInitials = (name: string | null | undefined) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className={cn(
        "flex h-full flex-col border-r border-[var(--border-color)] bg-[var(--bg-primary)]/95 backdrop-blur-xl text-[var(--text-primary)] transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}>
        {/* Logo */}
        <div className="flex h-14 items-center border-b px-3 justify-between">
          <Link href="/admin/bots" className={cn("flex items-center gap-2 font-semibold", isCollapsed && "justify-center")}>
            <div className="h-8 w-8 relative flex-shrink-0">
              <Image src="/profile-jelly.png" alt="Jelly ChatBot Logo" width={32} height={32} className="object-contain h-full w-full rounded-full" />
            </div>
            {!isCollapsed && (
              <span className="font-bold bg-clip-text text-transparent bg-gradient-to-r from-[var(--pink)] to-[var(--pink-light)]">Jelly ChatBot</span>
            )}
          </Link>
          {!isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 flex-shrink-0"
              onClick={toggleCollapsed}
            >
              <PanelLeftClose className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && (
          <div className="flex justify-center py-2 border-b border-[var(--border-color)]">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={toggleCollapsed}
            >
              <PanelLeft className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Navigation */}
        <div className="flex-1 py-4">
          <nav className={cn("grid gap-1", isCollapsed ? "px-2" : "px-2")}>
            {links.map((link) => (
              <Tooltip key={link.href}>
                <TooltipTrigger asChild>
                  <Link href={link.href}>
                    <Button
                      variant={pathname.startsWith(link.href) ? 'secondary' : 'ghost'}
                      className={cn(
                        "w-full gap-2 transition-all",
                        isCollapsed ? "justify-center px-2" : "justify-start",
                        pathname.startsWith(link.href) && "text-[var(--pink)] font-bold border border-[var(--border-color)]"
                      )}
                    >
                      <link.icon className="h-4 w-4 flex-shrink-0" />
                      {!isCollapsed && link.label}
                    </Button>
                  </Link>
                </TooltipTrigger>
                {isCollapsed && (
                  <TooltipContent side="right">
                    {link.label}
                  </TooltipContent>
                )}
              </Tooltip>
            ))}
          </nav>
          
          {/* API Connectivity Status - Guardrail */}
          <div className={cn("mt-auto px-4 py-4", isCollapsed && "px-2 flex justify-center")}>
             <ApiStatusIndicator isCollapsed={isCollapsed} />
          </div>
        </div>

        {/* User Section */}
        {session?.user && (
          <div className="border-t p-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className={cn(
                    "w-full h-auto py-2",
                    isCollapsed ? "justify-center px-0" : "justify-start gap-2"
                  )}
                >
                  <Avatar className="h-8 w-8 flex-shrink-0">
                    <AvatarImage src={session.user.image || undefined} alt={session.user.name || ''} />
                    <AvatarFallback className="bg-[var(--lavender)] text-white text-xs">
                      {getInitials(session.user.name)}
                    </AvatarFallback>
                  </Avatar>
                  {!isCollapsed && (
                    <>
                      <div className="flex flex-col items-start flex-1 min-w-0">
                        <span className="text-sm font-medium truncate w-full text-left">
                          {session.user.name}
                        </span>
                        <span className="text-xs text-muted-foreground truncate w-full text-left">
                          {session.user.email}
                        </span>
                      </div>
                      <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    </>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align={isCollapsed ? "center" : "end"} side={isCollapsed ? "right" : "top"} className="w-56">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{session.user.name}</p>
                  <p className="text-xs text-muted-foreground">{session.user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => signOut({ callbackUrl: '/login' })}
                  className="text-destructive focus:text-destructive cursor-pointer"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
