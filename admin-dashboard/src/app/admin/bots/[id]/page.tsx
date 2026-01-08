'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Upload, File as FileIcon, Trash } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

import { api, BotDetail, BotFile } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export default function BotDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const botId = params.id as string;
    const queryClient = useQueryClient();
    const [uploading, setUploading] = useState(false);

    const { data: bot, isLoading } = useQuery<BotDetail>({
        queryKey: ['bot', botId],
        queryFn: async () => {
            const response = await api.get(`/bots/${botId}`);
            return response.data;
        },
    });

    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            const formData = new FormData();
            formData.append('file', file);
            await api.post(`/bots/${botId}/files`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bot', botId] });
            toast.success('File uploaded successfully');
            setUploading(false);
        },
        onError: () => {
            toast.error('Failed to upload file');
            setUploading(false);
        },
    });

    const deleteFileMutation = useMutation({
        mutationFn: async (fileId: string) => {
            await api.delete(`/files/${fileId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bot', botId] });
            toast.success('File deleted successfully');
        },
        onError: () => {
            toast.error('Failed to delete file');
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setUploading(true);
            uploadMutation.mutate(e.target.files[0]);
        }
    };

    if (isLoading) {
        return <div className="p-8">Loading bot details...</div>;
    }

    if (!bot) {
        return <div className="p-8">Bot not found</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">{bot.name}</h2>
                    <p className="text-muted-foreground">{bot.description}</p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Configuration</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div className="font-medium text-muted-foreground">Bot ID</div>
                            <div className="col-span-2 font-mono">{bot.id}</div>
                            
                            <div className="font-medium text-muted-foreground">Channel ID</div>
                            <div className="col-span-2 font-mono">{bot.channel_id}</div>
                            
                            <div className="font-medium text-muted-foreground">Webhook URL</div>
                            <div className="col-span-2 font-mono break-all">{bot.webhook_url}</div>
                            
                            <div className="font-medium text-muted-foreground">Created</div>
                            <div className="col-span-2">{format(new Date(bot.created_at), 'PPP p')}</div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="md:col-span-2">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Knowledge Base Files</CardTitle>
                            <div className="flex items-center gap-2">
                                <Input
                                    type="file"
                                    className="hidden"
                                    id="file-upload"
                                    onChange={handleFileChange}
                                    disabled={uploading}
                                />
                                <Button asChild disabled={uploading}>
                                    <label htmlFor="file-upload" className="cursor-pointer">
                                        <Upload className="mr-2 h-4 w-4" />
                                        {uploading ? 'Uploading...' : 'Upload File'}
                                    </label>
                                </Button>
                            </div>
                        </div>
                        <CardDescription>
                            Upload text files (TXT, CSV, MD) to be used as knowledge base.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Filename</TableHead>
                                    <TableHead>Size</TableHead>
                                    <TableHead>Uploaded</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {bot.files?.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                                            No files uploaded yet.
                                        </TableCell>
                                    </TableRow>
                                )}
                                {bot.files?.map((file) => (
                                    <TableRow key={file.id}>
                                        <TableCell className="font-medium flex items-center gap-2">
                                            <FileIcon className="h-4 w-4 text-muted-foreground" />
                                            {file.filename}
                                        </TableCell>
                                        <TableCell>{(file.size_bytes ? file.size_bytes / 1024 : 0).toFixed(2)} KB</TableCell>
                                        <TableCell>{format(new Date(file.uploaded_at), 'PPP')}</TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-destructive"
                                                onClick={() => {
                                                    if(confirm('Delete this file?')) deleteFileMutation.mutate(file.id);
                                                }}
                                            >
                                                <Trash className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
