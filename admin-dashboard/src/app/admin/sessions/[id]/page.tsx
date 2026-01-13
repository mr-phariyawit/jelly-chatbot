'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, User, Bot } from 'lucide-react';

import { api, SessionDetail } from '@/lib/api';
import { useFormattedDate } from '@/hooks/use-formatted-date';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function SessionDetailsPage() {
    const { formatTimeOnly } = useFormattedDate();
    const params = useParams();
    const router = useRouter();
    const sessionId = params.id as string;

    const { data: session, isLoading } = useQuery<SessionDetail>({
        queryKey: ['session', sessionId],
        queryFn: async () => {
            const response = await api.get(`/sessions/${sessionId}`);
            return response.data;
        },
    });

    if (isLoading) {
        return <div className="p-8">Loading session chat...</div>;
    }

    if (!session) {
        return <div className="p-8">Session not found</div>;
    }

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div>
                     <div className="flex items-center gap-2">
                        <h2 className="text-3xl font-bold tracking-tight">Session Chat</h2>
                        <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                            {session.status}
                        </Badge>
                        {session.is_escalated && (
                            <Badge variant="destructive">Escalated</Badge>
                        )}
                    </div>
                    <p className="text-muted-foreground font-mono text-sm mt-1">
                        ID: {session.id} | User: {session.user_id}
                    </p>
                </div>
            </div>

            <Card className="h-[calc(100vh-200px)] flex flex-col">
                <CardHeader className="border-b">
                    <CardTitle>Message History</CardTitle>
                    <CardDescription>
                        Transcript of the conversation.
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                    {session.messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex ${
                                msg.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                        >
                            <div
                                className={`flex gap-3 max-w-[80%] ${
                                    msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                                }`}
                            >
                                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                                    msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                                }`}>
                                    {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                </div>
                                <div className={`rounded-lg p-3 text-sm ${
                                    msg.role === 'user' 
                                        ? 'bg-primary text-primary-foreground' 
                                        : 'bg-muted'
                                }`}>
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                    <div className={`text-[10px] mt-1 ${
                                        msg.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground'
                                    }`}>
                                        {formatTimeOnly(msg.timestamp)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    );
}
