'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { MessageSquare } from 'lucide-react';

import { api, Session, Bot } from '@/lib/api';
import { useFormattedDate } from '@/hooks/use-formatted-date';
import { Button } from '@/components/ui/button';
import { SessionsFilter } from '@/components/sessions/sessions-filter';
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
    const { formatRelative } = useFormattedDate();
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
    const [isGrouped, setIsGrouped] = useState(false);

    // Fetch Bots for filter
    const { data: bots } = useQuery<Bot[]>({
        queryKey: ['bots'],
        queryFn: async () => {
            const response = await api.get('/bots');
            return response.data;
        },
    });

    // Fetch Sessions with filters
    const { data: sessions, isLoading } = useQuery<Session[]>({
        queryKey: ['sessions', selectedBotId, selectedStatus],
        queryFn: async () => {
            const params: Record<string, string> = {};
            if (selectedBotId) params.bot_id = selectedBotId;
            if (selectedStatus) params.status = selectedStatus;
            
            const response = await api.get('/sessions', { params });
            return response.data;
        },
    });

    // Grouping Logic
    const groupedSessions = useMemo(() => {
        if (!sessions) return {};
        const groups: Record<string, Session[]> = {};
        
        sessions.forEach(session => {
            const botName = bots?.find(b => b.id === session.bot_id)?.name || 'Unknown Bot';
            if (!groups[botName]) groups[botName] = [];
            groups[botName].push(session);
        });

        return groups;
    }, [sessions, bots]);

    const handleReset = () => {
        setSelectedBotId(null);
        setSelectedStatus(null);
        setIsGrouped(false);
    };

    if (isLoading) {
        return <div className="p-8">Loading sessions...</div>;
    }

    const renderSessionRow = (session: Session) => (
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
            {!isGrouped && (
                <TableCell className="font-mono text-xs text-muted-foreground">
                    {bots?.find(b => b.id === session.bot_id)?.name || 'N/A'}
                </TableCell>
            )}
            <TableCell className="text-sm">
                {formatRelative(session.started_at)}
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
    );

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Sessions</h2>
                <p className="text-muted-foreground">
                    View and manage user chat sessions.
                </p>
            </div>

            <SessionsFilter 
                bots={bots || []}
                selectedBotId={selectedBotId}
                onSelectBot={setSelectedBotId}
                selectedStatus={selectedStatus}
                onSelectStatus={setSelectedStatus}
                isGrouped={isGrouped}
                onToggleGroup={setIsGrouped}
                onReset={handleReset}
            />

            {isGrouped ? (
                <div className="space-y-6">
                    {Object.entries(groupedSessions).map(([botName, sessions]) => (
                        <Card key={botName} className="overflow-hidden">
                            <CardHeader className="bg-muted/50 py-3">
                                <div className="flex items-center gap-2">
                                    <MessageSquare className="h-4 w-4 text-primary" />
                                    <CardTitle className="text-base font-medium">{botName}</CardTitle>
                                    <Badge variant="outline" className="ml-2">
                                        {sessions.length}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="p-0">
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Session ID</TableHead>
                                            <TableHead>User ID</TableHead>
                                            <TableHead>Started</TableHead>
                                            <TableHead className="text-right">Msgs</TableHead>
                                            <TableHead className="text-right">Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {sessions.map(renderSessionRow)}
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    ))}
                    {Object.keys(groupedSessions).length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                            No sessions found for the current filters.
                        </div>
                    )}
                </div>
            ) : (
                <Card>
                    <CardHeader>
                        <CardTitle>All Sessions</CardTitle>
                        <CardDescription>
                            Recent active sessions {selectedBotId ? 'for selected bot' : 'across all bots'}.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Session ID</TableHead>
                                    <TableHead>User ID</TableHead>
                                    <TableHead>Bot</TableHead>
                                    <TableHead>Started</TableHead>
                                    <TableHead className="text-right">Msgs</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {sessions?.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                            No sessions found.
                                        </TableCell>
                                    </TableRow>
                                )}
                                {sessions?.map(renderSessionRow)}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
