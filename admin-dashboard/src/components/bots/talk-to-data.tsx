'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Loader2, Bug, FileText, Bot, User, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';

import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { ChatMessage } from './chat/chat-message';
import { TypingIndicator } from './chat/typing-indicator';

interface ChatSource {
    filename: string;
    chunk_preview: string;
    similarity_score?: number;
}

interface ChatResponse {
    message: string;
    sources: ChatSource[];
    debug_info?: {
        system_prompt_preview: string;
        chunks_retrieved: any[];
        latency_ms: number;
        model: string;
    };
    token_usage?: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
    debug_info?: any;
    token_usage?: any;
}

interface TalkToDataProps {
    botId: string;
    botName?: string;
    systemPromptPreview?: string;
    fileCount?: number;
}

export function TalkToData({ botId, botName, systemPromptPreview, fileCount }: TalkToDataProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [debugMode, setDebugMode] = useState(false);
    const [expandedMessage, setExpandedMessage] = useState<number | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const chatMutation = useMutation({
        mutationFn: async (message: string) => {
            const response = await api.post<ChatResponse>(`/bots/${botId}/chat`, {
                message,
                debug: debugMode
            });
            return response.data;
        },
        onSuccess: (data) => {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.message,
                sources: data.sources,
                debug_info: data.debug_info,
                token_usage: data.token_usage
            }]);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Chat failed');
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `❌ Error: ${error.response?.data?.detail || 'Chat failed'}`
            }]);
        }
    });

    const handleSend = () => {
        if (!input.trim() || chatMutation.isPending) return;

        const userMessage = input.trim();
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setInput('');
        chatMutation.mutate(userMessage);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <Card className="flex flex-col h-[600px]">
            <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Bot className="h-5 w-5 text-purple-400" />
                            Talk to Data
                        </CardTitle>
                        <CardDescription>
                            Test your bot's responses with the RAG pipeline
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center space-x-2">
                            <Switch 
                                id="debug-mode" 
                                checked={debugMode} 
                                onCheckedChange={setDebugMode}
                            />
                            <Label htmlFor="debug-mode" className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Bug className="h-3 w-3" />
                                Debug Mode
                            </Label>
                        </div>
                        {fileCount !== undefined && (
                            <div className="text-xs text-muted-foreground">
                                <FileText className="h-3 w-3 inline mr-1" />
                                {fileCount} files indexed
                            </div>
                        )}
                    </div>
                </div>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-50">
                        <Bot className="h-16 w-16 mb-4 stroke-[1.5]" />
                        <p className="text-sm font-medium">Start a conversation to test your bot</p>
                        <p className="text-xs mt-1">Messages use the same RAG pipeline as LINE webhook</p>
                    </div>
                )}
                
                {messages.map((message, index) => (
                    <ChatMessage 
                        key={index}
                        role={message.role}
                        content={message.content}
                        sources={message.sources}
                        debug_info={message.debug_info}
                        token_usage={message.token_usage}
                        isLatest={index === messages.length - 1}
                    />
                ))}
                
                {chatMutation.isPending && (
                    <div className="flex gap-4 w-full justify-start">
                         <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg mt-1">
                            <Bot className="h-4 w-4 text-white" />
                        </div>
                        <div className="bg-background border border-border/50 rounded-2xl rounded-tl-none px-5 py-3 shadow-sm">
                            <TypingIndicator />
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </CardContent>
            
            <div className="p-4 border-t">
                <div className="flex gap-2">
                    <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a message to test your bot..."
                        className="min-h-[44px] max-h-[120px] resize-none"
                        disabled={chatMutation.isPending}
                    />
                    <Button 
                        onClick={handleSend} 
                        disabled={!input.trim() || chatMutation.isPending}
                        className="shrink-0"
                    >
                        {chatMutation.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>
            </div>
        </Card>
    );
}
