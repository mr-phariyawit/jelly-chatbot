'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { MoreHorizontal, Trash, FileText, MessageSquare, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

import { api, Bot } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { CreateBotDialog } from '@/components/bots/create-bot-dialog';
import { BotsPageSkeleton } from '@/components/bots/bot-skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function BotsPage() {
    const queryClient = useQueryClient();
    const { data: session } = useSession();
    const [botToDelete, setBotToDelete] = useState<string | null>(null);

    const { data: bots, isLoading } = useQuery<Bot[]>({
        queryKey: ['bots', session?.user?.email],
        queryFn: async () => {
             const config = session?.user?.email 
                ? { headers: { 'X-User-Email': session.user.email } } 
                : {};
            const response = await api.get('/bots', config);
            return response.data;
        },
        enabled: !!session?.user?.email,
        staleTime: 30 * 1000,      // Data fresh for 30 seconds
        gcTime: 5 * 60 * 1000,     // Keep in cache 5 minutes
        refetchOnWindowFocus: true, // Background refresh on tab focus
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/bots/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bots'] });
            toast.success('Bot deleted successfully');
        },
        onError: () => {
            toast.error('Failed to delete bot');
        },
    });

    if (isLoading) {
        return <BotsPageSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Bots</h2>
                    <p className="text-muted-foreground">
                        Manage your LINE bots and their configurations.
                    </p>
                </div>
                <CreateBotDialog />
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {bots?.map((bot) => (
                    <Card key={bot.id}>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <CardTitle className="truncate">{bot.name}</CardTitle>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" className="h-8 w-8 p-0">
                                            <span className="sr-only">Open menu</span>
                                            <MoreHorizontal className="h-4 w-4" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                        <DropdownMenuItem onClick={() => navigator.clipboard.writeText(bot.webhook_url)}>
                                            Copy Webhook URL
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem className="text-destructive" onClick={() => setBotToDelete(bot.id)}>
                                            <Trash className="mr-2 h-4 w-4" />
                                            Delete
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                            <CardDescription className="truncate">
                                {bot.description || 'No description'}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-col gap-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Status:</span>
                                    <Badge variant={bot.is_active ? 'default' : 'secondary'}>
                                        {bot.is_active ? 'Active' : 'Inactive'}
                                    </Badge>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Sessions:</span>
                                    <span>{bot.session_count}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Files:</span>
                                    <span>{bot.file_count}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Triggers:</span>
                                    <span className="truncate max-w-[120px] text-right" title={bot.trigger_names?.join(', ') || 'Default (Bot Name)'}>
                                        {bot.trigger_names && bot.trigger_names.length > 0 
                                            ? bot.trigger_names.join(', ') 
                                            : <span className="text-muted-foreground italic">Default</span>}
                                    </span>
                                </div>
                                <div className="mt-2 text-xs text-muted-foreground truncate" title={bot.webhook_url}>
                                    Webhook: ...{bot.webhook_path}
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="flex justify-between gap-2">
                             <Button asChild variant="outline" className="w-full">
                                <Link href={`/admin/bots/${bot.id}`}>
                                    <FileText className="mr-2 h-4 w-4" />
                                    Manage Files
                                </Link>
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            <AlertDialog open={!!botToDelete} onOpenChange={(open) => !open && setBotToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the bot and related data.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => {
                                if (botToDelete) {
                                    deleteMutation.mutate(botToDelete);
                                    setBotToDelete(null);
                                }
                            }}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
