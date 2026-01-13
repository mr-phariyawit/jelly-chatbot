'use client';

import { useQuery } from '@tanstack/react-query';
import { 
    MessageSquare, 
    Users, 
    FileText, 
    Bot, 
    Coins, 
    TrendingUp,
    AlertTriangle,
    Activity
} from 'lucide-react';

import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

interface AnalyticsOverview {
    total_messages: number;
    total_sessions: number;
    total_files: number;
    total_bots: number;
    total_tokens: number;
    estimated_cost_usd: number;
    active_users_7d: number;
}

interface TokenUsageStats {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
}

interface MessagesByDay {
    date: string;
    count: number;
}

interface AnalyticsDashboard {
    overview: AnalyticsOverview;
    token_usage: TokenUsageStats;
    messages_by_day: MessagesByDay[];
    top_bots: { id: string; name: string; message_count: number }[];
    recent_errors: number;
}

function KPICard({ 
    title, 
    value, 
    subtitle, 
    icon: Icon, 
    trend,
    color = 'purple'
}: { 
    title: string; 
    value: string | number; 
    subtitle?: string;
    icon: React.ElementType;
    trend?: string;
    color?: 'purple' | 'blue' | 'green' | 'yellow' | 'red';
}) {
    const colorClasses = {
        purple: 'bg-purple-500/20 text-purple-400',
        blue: 'bg-blue-500/20 text-blue-400',
        green: 'bg-green-500/20 text-green-400',
        yellow: 'bg-yellow-500/20 text-yellow-400',
        red: 'bg-red-500/20 text-red-400',
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                <div className={`h-8 w-8 rounded-full flex items-center justify-center ${colorClasses[color]}`}>
                    <Icon className="h-4 w-4" />
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {subtitle && (
                    <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
                )}
                {trend && (
                    <p className="text-xs text-green-500 mt-1 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> {trend}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}

function SimpleBarChart({ data, maxBars = 14 }: { data: MessagesByDay[]; maxBars?: number }) {
    const displayData = data.slice(-maxBars);
    const maxCount = Math.max(...displayData.map(d => d.count), 1);

    if (displayData.length === 0) {
        return (
            <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
                No message data available
            </div>
        );
    }

    return (
        <div className="flex items-end gap-1 h-40">
            {displayData.map((item, index) => (
                <div key={index} className="flex-1 flex flex-col items-center gap-1">
                    <div 
                        className="w-full bg-purple-500/60 rounded-t hover:bg-purple-500 transition-colors"
                        style={{ height: `${(item.count / maxCount) * 100}%`, minHeight: item.count > 0 ? '4px' : '0' }}
                        title={`${item.date}: ${item.count} messages`}
                    />
                    <span className="text-[10px] text-muted-foreground truncate w-full text-center">
                        {new Date(item.date).getDate()}
                    </span>
                </div>
            ))}
        </div>
    );
}

function TokenPieChart({ prompt, completion }: { prompt: number; completion: number }) {
    const total = prompt + completion;
    const promptPercent = total > 0 ? (prompt / total) * 100 : 50;
    
    return (
        <div className="flex items-center gap-6">
            <div className="relative w-24 h-24">
                <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                    <circle
                        cx="18"
                        cy="18"
                        r="15.915"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        className="text-muted"
                    />
                    <circle
                        cx="18"
                        cy="18"
                        r="15.915"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeDasharray={`${promptPercent} ${100 - promptPercent}`}
                        className="text-blue-500"
                    />
                    <circle
                        cx="18"
                        cy="18"
                        r="15.915"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeDasharray={`${100 - promptPercent} ${promptPercent}`}
                        strokeDashoffset={`-${promptPercent}`}
                        className="text-purple-500"
                    />
                </svg>
            </div>
            <div className="space-y-2">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded" />
                    <span className="text-sm">Prompt: {prompt.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-purple-500 rounded" />
                    <span className="text-sm">Completion: {completion.toLocaleString()}</span>
                </div>
            </div>
        </div>
    );
}

export default function AnalyticsPage() {
    const { data, isLoading, error } = useQuery<AnalyticsDashboard>({
        queryKey: ['analytics-dashboard'],
        queryFn: async () => {
            const response = await api.get('/analytics/dashboard');
            return response.data;
        },
        refetchInterval: 60000, // Refresh every minute
    });

    if (isLoading) {
        return (
            <div className="flex flex-col gap-6">
                <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {[...Array(4)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader className="pb-2">
                                <div className="h-4 bg-muted rounded w-24" />
                            </CardHeader>
                            <CardContent>
                                <div className="h-8 bg-muted rounded w-16" />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="flex flex-col gap-6">
                <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
                <Card>
                    <CardContent className="flex items-center justify-center py-8">
                        <p className="text-muted-foreground">Failed to load analytics data</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const { overview, token_usage, messages_by_day, top_bots, recent_errors } = data;

    return (
        <div className="flex flex-col gap-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Analytics Dashboard</h1>
                <p className="text-muted-foreground">360° view of your platform performance</p>
            </div>

            {/* KPI Cards Row 1 */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KPICard
                    title="Total Messages"
                    value={overview.total_messages.toLocaleString()}
                    subtitle={`${overview.total_sessions} sessions`}
                    icon={MessageSquare}
                    color="blue"
                />
                <KPICard
                    title="Active Users (7d)"
                    value={overview.active_users_7d}
                    subtitle="Unique users this week"
                    icon={Users}
                    color="green"
                />
                <KPICard
                    title="Knowledge Base"
                    value={overview.total_files}
                    subtitle={`Across ${overview.total_bots} bot(s)`}
                    icon={FileText}
                    color="purple"
                />
                <KPICard
                    title="Recent Errors"
                    value={recent_errors}
                    subtitle="Last 7 days"
                    icon={AlertTriangle}
                    color={recent_errors > 5 ? 'red' : 'yellow'}
                />
            </div>

            {/* KPI Cards Row 2 - Token Usage */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KPICard
                    title="Total Tokens"
                    value={token_usage.total_tokens.toLocaleString()}
                    subtitle="Last 30 days"
                    icon={Activity}
                    color="purple"
                />
                <KPICard
                    title="Prompt Tokens"
                    value={token_usage.prompt_tokens.toLocaleString()}
                    subtitle={`${((token_usage.prompt_tokens / (token_usage.total_tokens || 1)) * 100).toFixed(1)}% of total`}
                    icon={Coins}
                    color="blue"
                />
                <KPICard
                    title="Completion Tokens"
                    value={token_usage.completion_tokens.toLocaleString()}
                    subtitle={`${((token_usage.completion_tokens / (token_usage.total_tokens || 1)) * 100).toFixed(1)}% of total`}
                    icon={Coins}
                    color="green"
                />
                <KPICard
                    title="Estimated Cost"
                    value={`$${token_usage.estimated_cost_usd.toFixed(4)}`}
                    subtitle="Gemini 2.0 Flash pricing"
                    icon={TrendingUp}
                    color="yellow"
                />
            </div>

            {/* Charts Row */}
            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Messages Over Time</CardTitle>
                        <CardDescription>Daily message count for the last 14 days</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <SimpleBarChart data={messages_by_day} />
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Token Distribution</CardTitle>
                        <CardDescription>Prompt vs Completion tokens (30 days)</CardDescription>
                    </CardHeader>
                    <CardContent className="flex items-center justify-center pt-4">
                        <TokenPieChart 
                            prompt={token_usage.prompt_tokens} 
                            completion={token_usage.completion_tokens} 
                        />
                    </CardContent>
                </Card>
            </div>

            {/* Top Bots */}
            {top_bots.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Top Bots by Usage</CardTitle>
                        <CardDescription>Most active bots by message count</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {top_bots.map((bot, index) => (
                                <div key={bot.id} className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold text-sm">
                                            {index + 1}
                                        </div>
                                        <div>
                                            <p className="font-medium">{bot.name}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {bot.message_count.toLocaleString()} messages
                                            </p>
                                        </div>
                                    </div>
                                    <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                                        <div 
                                            className="h-full bg-purple-500"
                                            style={{ 
                                                width: `${(bot.message_count / (top_bots[0]?.message_count || 1)) * 100}%` 
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
