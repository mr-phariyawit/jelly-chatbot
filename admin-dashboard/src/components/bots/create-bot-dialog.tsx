'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
import { api } from '@/lib/api';

interface CreateBotForm {
    name: string;
    description: string;
    channel_id: string;
    channel_secret: string;
    channel_access_token: string;
    user_id?: string;
    system_prompt?: string;
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
        },
    });

    const mutation = useMutation({
        mutationFn: async (data: CreateBotForm) => {
            const config = session?.user?.email 
                ? { headers: { 'X-User-Email': session.user.email } } 
                : {};
            const response = await api.post('/bots', data, config);
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
                <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Bot
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Create New Bot</DialogTitle>
                    <DialogDescription>
                        Enter your LINE Bot credentials here.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="name"
                            rules={{ required: 'Name is required' }}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Bot Name</FormLabel>
                                    <FormControl>
                                        <Input placeholder="My AI Assistant" {...field} />
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
                                        <Textarea placeholder="Bot description..." {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <div className="grid grid-cols-2 gap-4">
                             <FormField
                                control={form.control}
                                name="channel_id"
                                rules={{ required: 'Channel ID is required' }}
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Channel ID</FormLabel>
                                        <FormControl>
                                            <Input placeholder="1234567890" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="user_id"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Owner User ID (Optional)</FormLabel>
                                        <FormControl>
                                            <Input placeholder="U..." {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <FormField
                            control={form.control}
                            name="channel_secret"
                            rules={{ required: 'Channel Secret is required' }}
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Channel Secret</FormLabel>
                                    <FormControl>
                                        <Input type="password" placeholder="e.g. 8f..." {...field} />
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
                                        <Textarea className="h-20" placeholder="Long-lived access token" {...field} />
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
                                    <FormLabel>System Prompt (Optional)</FormLabel>
                                    <FormControl>
                                        <Textarea 
                                            className="h-32" 
                                            placeholder="กำหนด personality ของ Bot เช่น 'คุณคือ AI Assistant ของบริษัท XYZ ทำหน้าที่ช่วยเหลือลูกค้า...'" 
                                            {...field} 
                                        />
                                    </FormControl>
                                    <FormDescription>
                                        กำหนดบุคลิกและพฤติกรรมของ Bot ถ้าไม่ใส่จะใช้ค่าเริ่มต้น
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <DialogFooter>
                            <Button type="submit" disabled={mutation.isPending}>
                                {mutation.isPending ? 'Creating...' : 'Create Bot'}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
