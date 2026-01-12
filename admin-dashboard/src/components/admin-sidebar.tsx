'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { LayoutDashboard, MessageSquare, Bot, LogOut, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function AdminSidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

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
    <div className="flex h-full w-64 flex-col border-r border-[var(--border-color)] bg-[var(--bg-primary)]/95 backdrop-blur-xl text-[var(--text-primary)]">
        {/* Logo */}
        <div className="flex h-14 items-center border-b px-4">
            <Link href="/admin/bots" className="flex items-center gap-2 font-semibold">
                <div className="h-8 w-8 relative">
                    <img src="/logo.svg" alt="AI Platform Logo" className="object-contain h-full w-full" />
                </div>
                <span className="font-bold bg-clip-text text-transparent bg-gradient-to-r from-[var(--gold)] to-[var(--gold-light)]">AI Support</span>
            </Link>
        </div>

        {/* Navigation */}
        <div className="flex-1 py-4">
            <nav className="grid gap-1 px-2">
                {links.map((link) => (
                    <Link key={link.href} href={link.href}>
                        <Button
                            variant={pathname.startsWith(link.href) ? 'secondary' : 'ghost'}
                            className={cn("w-full justify-start gap-2", pathname.startsWith(link.href) && "text-[var(--gold)] font-bold border border-[var(--border-color)]")}
                        >
                            <link.icon className="h-4 w-4" />
                            {link.label}
                        </Button>
                    </Link>
                ))}
            </nav>
        </div>

        {/* User Section */}
        {session?.user && (
            <div className="border-t p-4">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="w-full justify-start gap-2 h-auto py-2">
                            <Avatar className="h-8 w-8">
                                <AvatarImage src={session.user.image || undefined} alt={session.user.name || ''} />
                                <AvatarFallback className="bg-[var(--purple)] text-white text-xs">
                                    {getInitials(session.user.name)}
                                </AvatarFallback>
                            </Avatar>
                            <div className="flex flex-col items-start flex-1 min-w-0">
                                <span className="text-sm font-medium truncate w-full text-left">
                                    {session.user.name}
                                </span>
                                <span className="text-xs text-muted-foreground truncate w-full text-left">
                                    {session.user.email}
                                </span>
                            </div>
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
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
  );
}
