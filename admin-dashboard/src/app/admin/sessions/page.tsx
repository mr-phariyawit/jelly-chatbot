'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { format } from 'date-fns';
import { MessageSquare, Users, AlertCircle } from 'lucide-react';

import { api, Session } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export default function SessionsPage() {
    const { data: sessions, isLoading } = useQuery<Session[]>({
        queryKey: ['sessions'],
        queryFn: async () => {
            const response = await api.get('/sessions');
            return response.data;
        },
    });

    if (isLoading) {
        return <div className="p-8">Loading sessions...</div>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
                <p className="text-muted-foreground">
                    View and manage user chat sessions.
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>All Sessions</CardTitle>
                    <CardDescription>
                        Recent active sessions across all bots.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Status</TableHead>
                                <TableHead>Session ID</TableHead>
                                <TableHead>User ID</TableHead>
                                <TableHead>Bot ID</TableHead>
                                <TableHead>Started</TableHead>
                                <TableHead className="text-right">Msgs</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {sessions?.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                        No active sessions found.
                                    </TableCell>
                                </TableRow>
                            )}
                            {sessions?.map((session) => (
                                <TableRow key={session.id}>
                                    <TableCell>
                                        <div className="flex flex-col gap-1">
                                             <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                                                {session.status}
                                            </Badge>
                                            {session.is_escalated && (
                                                <Badge variant="destructive" className="w-fit">
                                                    Escalated
                                                </Badge>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="font-mono text-xs">{session.id}</TableCell>
                                    <TableCell className="font-mono text-xs">{session.user_id}</TableCell>
                                    <TableCell className="font-mono text-xs text-muted-foreground">
                                        {session.bot_id ? session.bot_id.substring(0, 8) + '...' : 'N/A'}
                                    </TableCell>
                                    <TableCell className="text-sm">
                                        {format(new Date(session.started_at), 'PP p')}
                                    </TableCell>
                                    <TableCell className="text-right">{session.message_count}</TableCell>
                                    <TableCell className="text-right">
                                        <Button asChild variant="ghost" size="sm">
                                            <Link href={`/admin/sessions/${session.id}`}>
                                                View
                                            </Link>
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
