'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { 
  Plus, 
  Bot, 
  FileText, 
  Settings2, 
  Key, 
  Hash, 
  Lock, 
  Fingerprint, 
  AtSign 
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';

interface CreateBotForm {
    name: string;
    description: string;
    channel_id: string;
    channel_secret: string;
    channel_access_token: string;
    user_id?: string;
    system_prompt?: string;
    trigger_names_input?: string; // Comma separated string
}

export function CreateBotDialog() {
    const [open, setOpen] = useState(false);
    const { data: session } = useSession();
    const queryClient = useQueryClient();

    const form = useForm<CreateBotForm>({
        defaultValues: {
            name: '',
            description: '',
            channel_id: '',
            channel_secret: '',
            channel_access_token: '',
            user_id: '',
            system_prompt: '',
            trigger_names_input: '',
        },
    });

    const mutation = useMutation({
        mutationFn: async (data: CreateBotForm) => {
            const config = session?.user?.email 
                ? { headers: { 'X-User-Email': session.user.email } } 
                : {};
            
            // Transform trigger_names_input to array
            const trigger_names = data.trigger_names_input 
                ? data.trigger_names_input.split(',').map(s => s.trim()).filter(s => s.length > 0)
                : undefined;

            // eslint-disable-next-line @typescript-eslint/no-unused-vars -- Destructuring to omit trigger_names_input from payload
            const { trigger_names_input: _unused, ...restData } = data;
            const payload = {
                ...restData,
                trigger_names
            };

            const response = await api.post('/bots', payload, config);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bots'] });
            setOpen(false);
            form.reset();
            toast.success('Bot created successfully');
        },
        onError: (error) => {
            toast.error('Failed to create bot');
            console.error(error);
        },
    });

    const onSubmit = (data: CreateBotForm) => {
        mutation.mutate(data);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Bot
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-2xl max-h-[90vh] p-0 gap-0 overflow-hidden">
                <DialogHeader className="p-6 pb-4 border-b">
                    <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                        Create New Bot
                    </DialogTitle>
                    <DialogDescription>
                        Configure your new AI assistant and connect it to LINE.
                    </DialogDescription>
                </DialogHeader>
                
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col h-full">
                        <ScrollArea className="max-h-[60vh] px-6 py-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Left Column: Bot Identity */}
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Bot className="h-5 w-5 text-blue-500" />
                                        <h3 className="font-semibold text-lg">Bot Identity</h3>
                                    </div>
                                    <Card className="border-none shadow-sm bg-slate-50 dark:bg-slate-900/50">
                                        <CardContent className="p-4 space-y-4">
                                            <FormField
                                                control={form.control}
                                                name="name"
                                                rules={{ required: 'Name is required' }}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Bot Name</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Bot className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Input placeholder="My AI Assistant" className="pl-9" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                            
                                            <FormField
                                                control={form.control}
                                                name="description"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Description</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <FileText className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Textarea placeholder="What does this bot do?" className="pl-9 min-h-[80px]" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name="system_prompt"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>System Prompt</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Settings2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                                                <Textarea 
                                                                    className="pl-9 min-h-[120px] font-mono text-sm" 
                                                                    placeholder="You are a helpful assistant..." 
                                                                    {...field} 
                                                                />
                                                            </div>
                                                        </FormControl>
                                                        <FormDescription className="text-xs">
                                                            Define personality and behavior rules.
                                                        </FormDescription>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                        </CardContent>
                                    </Card>

                                    {/* Optional Triggers */}
                                    <Card className="border-none shadow-sm bg-slate-50 dark:bg-slate-900/50">
                                        <CardContent className="p-4">
                                             <FormField
                                                control={form.control}
                                                name="trigger_names_input"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Trigger Names (Optional)</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <AtSign className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Input placeholder="@bot, helper" className="pl-9" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormDescription className="text-xs">
                                                            Comma-separated names for group chat triggers.
                                                        </FormDescription>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                        </CardContent>
                                    </Card>
                                </div>

                                {/* Right Column: LINE Configuration */}
                                <div className="space-y-4">
                                     <div className="flex items-center gap-2 mb-2">
                                        <div className="h-5 w-5 rounded bg-[#06C755] flex items-center justify-center text-white font-bold text-[10px]">LINE</div>
                                        <h3 className="font-semibold text-lg">LINE Configuration</h3>
                                    </div>
                                    <Card className="border-none shadow-sm bg-slate-50 dark:bg-slate-900/50">
                                        <CardContent className="p-4 space-y-4">
                                            <FormField
                                                control={form.control}
                                                name="channel_id"
                                                rules={{ required: 'Channel ID is required' }}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Channel ID</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Hash className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Input placeholder="1234567890" className="pl-9 font-mono" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name="channel_secret"
                                                rules={{ required: 'Channel Secret is required' }}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Channel Secret</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Input type="password" placeholder="e.g. 8f..." className="pl-9 font-mono" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name="channel_access_token"
                                                rules={{ required: 'Access Token is required' }}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Channel Access Token</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Key className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                                                <Textarea className="pl-9 min-h-[160px] font-mono text-xs break-all" placeholder="Long-lived access token" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                             <Separator className="my-2" />
                                             
                                             <FormField
                                                control={form.control}
                                                name="user_id"
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Owner User ID (Optional)</FormLabel>
                                                        <FormControl>
                                                            <div className="relative">
                                                                <Fingerprint className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <Input placeholder="U..." className="pl-9 font-mono" {...field} />
                                                            </div>
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>
                        </ScrollArea>
                        
                        <div className="mt-auto border-t p-6 bg-slate-50/50 dark:bg-slate-900/50 flex justify-end gap-3 rounded-b-lg">
                            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                                Cancel
                            </Button>
                            <Button type="submit" disabled={mutation.isPending} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white min-w-[120px]">
                                {mutation.isPending ? 'Creating...' : 'Create Bot'}
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
