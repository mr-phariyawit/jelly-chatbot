'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { RefreshCw, Trash2, AlertCircle, Info, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';

import { botLogsApi, BotLog, BotLogStats } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

interface BotLogViewerProps {
    botId: string;
}

const levelIcons = {
    INFO: <Info className="h-4 w-4 text-blue-500" />,
    WARN: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
    ERROR: <AlertCircle className="h-4 w-4 text-red-500" />,
};

const levelColors: Record<string, string> = {
    INFO: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    WARN: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    ERROR: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const eventTypeColors: Record<string, string> = {
    WEBHOOK: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    LLM_CALL: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    RAG_SEARCH: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
    JIRA: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    ERROR: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export function BotLogViewer({ botId }: BotLogViewerProps) {
    const queryClient = useQueryClient();
    const [levelFilter, setLevelFilter] = useState<string>('all');
    const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
    const [page, setPage] = useState(1);
    const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

    const { data: logsData, isLoading: logsLoading, refetch } = useQuery({
        queryKey: ['bot-logs', botId, levelFilter, eventTypeFilter, page],
        queryFn: async () => {
            return botLogsApi.getLogs(botId, {
                level: levelFilter !== 'all' ? levelFilter : undefined,
                event_type: eventTypeFilter !== 'all' ? eventTypeFilter : undefined,
                page,
                page_size: 20,
            });
        },
    });

    const { data: stats } = useQuery({
        queryKey: ['bot-logs-stats', botId],
        queryFn: () => botLogsApi.getLogStats(botId),
    });

    const clearLogsMutation = useMutation({
        mutationFn: (days: number) => botLogsApi.clearLogs(botId, days),
        onSuccess: (data) => {
            toast.success(data.message);
            queryClient.invalidateQueries({ queryKey: ['bot-logs', botId] });
            queryClient.invalidateQueries({ queryKey: ['bot-logs-stats', botId] });
        },
        onError: () => {
            toast.error('Failed to clear logs');
        },
    });

    const parseMetadata = (metadata?: string) => {
        if (!metadata) return null;
        try {
            return JSON.parse(metadata);
        } catch {
            return null;
        }
    };

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Total Logs</CardDescription>
                        <CardTitle className="text-3xl">{stats?.total ?? 0}</CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Info</CardDescription>
                        <CardTitle className="text-3xl text-blue-500">{stats?.by_level.INFO ?? 0}</CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Warnings</CardDescription>
                        <CardTitle className="text-3xl text-yellow-500">{stats?.by_level.WARN ?? 0}</CardTitle>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader className="pb-2">
                        <CardDescription>Errors</CardDescription>
                        <CardTitle className="text-3xl text-red-500">{stats?.by_level.ERROR ?? 0}</CardTitle>
                    </CardHeader>
                </Card>
            </div>

            {/* Logs Table */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <CardTitle>Technical Logs</CardTitle>
                            <CardDescription>System events, API calls, and errors</CardDescription>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                            <select
                                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                                value={levelFilter}
                                onChange={(e) => setLevelFilter(e.target.value)}
                            >
                                <option value="all">All Levels</option>
                                <option value="INFO">Info</option>
                                <option value="WARN">Warning</option>
                                <option value="ERROR">Error</option>
                            </select>
                            <select
                                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                                value={eventTypeFilter}
                                onChange={(e) => setEventTypeFilter(e.target.value)}
                            >
                                <option value="all">All Events</option>
                                <option value="WEBHOOK">Webhook</option>
                                <option value="LLM_CALL">LLM Call</option>
                                <option value="RAG_SEARCH">RAG Search</option>
                                <option value="JIRA">JIRA</option>
                                <option value="ERROR">Error</option>
                            </select>
                            <Button variant="outline" size="icon" onClick={() => refetch()}>
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => {
                                    if (confirm('Clear logs older than 7 days?')) {
                                        clearLogsMutation.mutate(7);
                                    }
                                }}
                            >
                                <Trash2 className="h-4 w-4 mr-1" />
                                Clear Old
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {logsLoading ? (
                        <div className="text-center py-8 text-muted-foreground">Loading logs...</div>
                    ) : (
                        <>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[50px]"></TableHead>
                                        <TableHead className="w-[180px]">Timestamp</TableHead>
                                        <TableHead className="w-[80px]">Level</TableHead>
                                        <TableHead className="w-[120px]">Event Type</TableHead>
                                        <TableHead>Message</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {logsData?.logs.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                                                No logs found.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {logsData?.logs.map((log) => (
                                        <TableRow
                                            key={log.id}
                                            className="cursor-pointer hover:bg-muted/50"
                                            onClick={() => setExpandedLogId(expandedLogId === log.id ? null : log.id)}
                                        >
                                            <TableCell>
                                                {log.metadata ? (
                                                    expandedLogId === log.id ? (
                                                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                                                    ) : (
                                                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                                    )
                                                ) : null}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">
                                                {format(new Date(log.created_at), 'yyyy-MM-dd HH:mm:ss')}
                                            </TableCell>
                                            <TableCell>
                                                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${levelColors[log.level] || ''}`}>
                                                    {levelIcons[log.level as keyof typeof levelIcons]}
                                                    {log.level}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${eventTypeColors[log.event_type] || 'bg-gray-100 text-gray-800'}`}>
                                                    {log.event_type}
                                                </span>
                                            </TableCell>
                                            <TableCell className="max-w-md truncate">{log.message}</TableCell>
                                        </TableRow>
                                    ))}
                                    {/* Expanded metadata rows */}
                                    {logsData?.logs.filter(log => expandedLogId === log.id && log.metadata).map(log => (
                                        <TableRow key={`${log.id}-metadata`}>
                                            <TableCell colSpan={5} className="bg-muted/30">
                                                <pre className="text-xs font-mono overflow-x-auto p-3 rounded bg-muted whitespace-pre-wrap">
                                                    {JSON.stringify(parseMetadata(log.metadata), null, 2)}
                                                </pre>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>

                            {/* Pagination */}
                            {logsData && logsData.total > 20 && (
                                <div className="flex items-center justify-between mt-4">
                                    <div className="text-sm text-muted-foreground">
                                        Page {page} of {Math.ceil(logsData.total / 20)}
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={page === 1}
                                            onClick={() => setPage(p => p - 1)}
                                        >
                                            Previous
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={page >= Math.ceil(logsData.total / 20)}
                                            onClick={() => setPage(p => p + 1)}
                                        >
                                            Next
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
