import { useState, useEffect } from 'react';
import { Bot, User, Copy, Check, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChatSource {
    filename: string;
    chunk_preview: string;
}

interface DebugInfo {
    model?: string;
    latency_ms?: number;
    system_prompt_preview?: string;
}

interface TokenUsage {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
}

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
    debug_info?: DebugInfo;
    token_usage?: TokenUsage;
    isLatest?: boolean; // To trigger typewriter only on new messages
}

export function ChatMessage({ role, content, sources, debug_info, token_usage, isLatest }: ChatMessageProps) {
    const [displayedContent, setDisplayedContent] = useState(role === 'user' ? content : '');
    const [isTyping, setIsTyping] = useState(role === 'assistant' && isLatest);
    const [expandedSources, setExpandedSources] = useState(false);
    const [copied, setCopied] = useState(false);

    // Typewriter Effect
    useEffect(() => {
        if (role === 'user') {
            setDisplayedContent(content);
            return;
        }

        if (isLatest) {
            let i = 0;
            const speed = 10; // ms per char
            setIsTyping(true);
            setDisplayedContent('');

            const interval = setInterval(() => {
                setDisplayedContent(content.slice(0, i + 1));
                i++;
                if (i >= content.length) {
                    clearInterval(interval);
                    setIsTyping(false);
                }
            }, speed);

            return () => clearInterval(interval);
        } else {
            setDisplayedContent(content);
            setIsTyping(false);
        }
    }, [content, isLatest, role]);

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={cn("flex gap-4 w-full", role === 'user' ? "justify-end" : "justify-start")}>
            {/* Assistant Avatar */}
            {role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg mt-1">
                    <Bot className="h-4 w-4 text-white" />
                </div>
            )}

            <div className={cn("flex flex-col max-w-[85%]", role === 'user' && "items-end")}>
                
                {/* Message Bubble */}
                <div
                    className={cn(
                        "relative group rounded-2xl px-5 py-3 shadow-sm text-sm leading-relaxed",
                        role === 'user'
                            ? "bg-blue-600 text-white rounded-tr-none"
                            : "bg-background border border-border/50 text-foreground rounded-tl-none shadow-sm dark:bg-muted/30"
                    )}
                >
                    {/* Copy Button (Hover) */}
                    {role === 'assistant' && !isTyping && (
                        <Button
                            size="icon"
                            variant="ghost"
                            className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground hover:bg-muted/50"
                            onClick={handleCopy}
                        >
                            {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                        </Button>
                    )}

                    {role === 'assistant' ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-pre:bg-muted/50 prose-pre:border prose-pre:border-border/50">
                            <ReactMarkdown>{displayedContent}</ReactMarkdown>
                            {isTyping && <span className="inline-block w-1.5 h-4 bg-purple-400 animate-pulse ml-1 align-middle" />}
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap">{content}</div>
                    )}
                </div>

                {/* Sources Section */}
                {sources && sources.length > 0 && (
                    <div className="mt-2 ml-1">
                        <button
                            onClick={() => setExpandedSources(!expandedSources)}
                            className="flex items-center gap-1.5 text-xs text-muted-foreground/70 hover:text-primary transition-colors bg-muted/30 px-2 py-1 rounded-full border border-transparent hover:border-border/50"
                        >
                            <FileText className="h-3 w-3" />
                            {sources.length} sources used
                            {expandedSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        </button>

                        {expandedSources && (
                            <div className="mt-2 grid gap-2 w-full max-w-md animate-in fade-in slide-in-from-top-2 duration-200">
                                {sources.map((source, i) => (
                                    <div key={i} className="bg-muted/40 border border-border/40 rounded-lg p-3 text-xs shadow-sm">
                                        <div className="font-medium text-purple-400 mb-1 flex items-center gap-2">
                                            <FileText className="h-3 w-3" />
                                            {source.filename}
                                        </div>
                                        <div className="text-muted-foreground/80 line-clamp-3 bg-background/50 p-2 rounded border border-border/20 font-mono">
                                            {source.chunk_preview}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Debug Info */}
                {(debug_info || token_usage) && (
                    <div className="text-[10px] text-muted-foreground/40 mt-1 px-1">
                        {token_usage?.total_tokens && `Tokens: ${token_usage.total_tokens} | `}
                        {debug_info?.model && `Model: ${debug_info.model} | `}
                        {debug_info?.latency_ms && `Latency: ${debug_info.latency_ms}ms`}
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1 dark:bg-blue-900/30">
                    <User className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
            )}
        </div>
    );
}
