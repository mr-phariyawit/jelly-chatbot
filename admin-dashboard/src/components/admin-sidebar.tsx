'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, MessageSquare, Bot, Users, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export function AdminSidebar() {
  const pathname = usePathname();

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

  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
        <div className="flex h-14 items-center border-b px-4">
            <Link href="/" className="flex items-center gap-2 font-semibold">
                <Bot className="h-6 w-6" />
                <span>AI Support Admin</span>
            </Link>
        </div>
        <div className="flex-1 py-4">
            <nav className="grid gap-1 px-2">
                {links.map((link) => (
                    <Link key={link.href} href={link.href}>
                        <Button
                            variant={pathname.startsWith(link.href) ? 'secondary' : 'ghost'}
                            className="w-full justify-start gap-2"
                        >
                            <link.icon className="h-4 w-4" />
                            {link.label}
                        </Button>
                    </Link>
                ))}
            </nav>
        </div>
    </div>
  );
}
