'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Upload, File as FileIcon, Trash, Settings, ScrollText, Pencil, Check, X, Wand2, Loader2, Bot } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';

import { api, BotDetail, BotFile, botApi, fileApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
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
import { BotLogViewer } from '@/components/bots/bot-log-viewer';
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


import { FileContextModal } from '@/components/bots/file-context-modal';
import { TalkToData } from '@/components/bots/talk-to-data';

// Component for individual file row to manage state
function FileTableRow({ file, onDelete }: { file: BotFile, onDelete: (id: string) => void }) {
    const [description, setDescription] = useState(file.description || '');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    // Sync local state when file prop updates (e.g. after invalidation)
    useState(() => {
        setDescription(file.description || '');
    });

    const queryClient = useQueryClient();

    const updateFileMutation = useMutation({
        mutationFn: async (desc: string) => {
            await fileApi.updateFile(file.id, { description: desc });
        },
        onSuccess: () => {
             toast.success('File description updated');
             queryClient.invalidateQueries({ queryKey: ['bot', file.bot_id] });
             setIsModalOpen(false); // Close modal on save
        },
        onError: () => toast.error('Failed to update description')
    });

    const analyzeFileMutation = useMutation({
        mutationFn: async () => {
             setIsAnalyzing(true);
             return await fileApi.analyzeFile(file.id);
        },
        onSuccess: (data) => {
             setDescription(data.summary);
             setIsAnalyzing(false);
             toast.success('AI Analysis result auto-saved!');
             queryClient.invalidateQueries({ queryKey: ['bot', file.bot_id] });
             // Open modal to let user review/enrich
             setIsModalOpen(true);
        },
        onError: () => {
             setIsAnalyzing(false);
             toast.error('AI Analysis failed');
        }
    });

    return (
        <>
            <TableRow key={file.id}>
                <TableCell className="font-medium flex items-center gap-2">
                    <FileIcon className="h-4 w-4 text-muted-foreground" />
                    <div className="flex flex-col">
                        <span>{file.filename}</span>
                        <span className="text-xs text-muted-foreground">{(file.size_bytes ? file.size_bytes / 1024 : 0).toFixed(2)} KB</span>
                    </div>
                </TableCell>
                <TableCell>
                    {(!file.status || file.status === 'completed' || file.status === 'indexed') ? (
                        <div className="flex items-center text-green-600 text-xs font-medium">
                            <Check className="h-3 w-3 mr-1" /> Ready
                        </div>
                    ) : (file.status === 'failed') ? (
                        <div className="flex items-center text-red-500 text-xs font-medium" title={file.description}>
                            <X className="h-3 w-3 mr-1" /> Failed
                        </div>
                    ) : (
                        <div className="flex items-center text-blue-500 text-xs font-medium animate-pulse">
                            <Loader2 className="h-3 w-3 mr-1 animate-spin" /> {file.status}
                        </div>
                    )}
                </TableCell>
                <TableCell>
                    <div className="flex items-center gap-2">
                        <div 
                            className="text-xs text-muted-foreground truncate max-w-[300px] cursor-pointer hover:text-foreground border border-transparent hover:border-border rounded px-2 py-1 transition-colors"
                            onClick={() => setIsModalOpen(true)}
                            title={description || "No context defined"}
                        >
                            {description || <span className="italic text-muted-foreground/50">Click to add context...</span>}
                        </div>
                        
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-purple-400 hover:text-purple-300 hover:bg-purple-900/20 shrink-0"
                            onClick={() => analyzeFileMutation.mutate()}
                            disabled={isAnalyzing}
                            title="Auto-Analyze & Enrich"
                        >
                            <Wand2 className={`h-3.5 w-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground shrink-0"
                            onClick={() => setIsModalOpen(true)}
                        >
                            <Pencil className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                </TableCell>
                <TableCell>{format(new Date(file.uploaded_at), 'PPP')}</TableCell>
                <TableCell className="text-right">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => onDelete(file.id)}
                    >
                        <Trash className="h-4 w-4" />
                    </Button>
                </TableCell>
            </TableRow>

            <FileContextModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={(newDesc) => updateFileMutation.mutate(newDesc)}
                initialDescription={description}
                filename={file.filename}
                isAnalyzing={isAnalyzing}
                onReAnalyze={() => analyzeFileMutation.mutate()}
                isSaving={updateFileMutation.isPending}
            />
        </>
    );
}

type TabType = 'overview' | 'files' | 'logs' | 'chat';

export default function BotDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const botId = params.id as string;
    const queryClient = useQueryClient();
    const [uploading, setUploading] = useState(false);
    const [activeTab, setActiveTab] = useState<TabType>('overview');
    const [fileToDelete, setFileToDelete] = useState<string | null>(null);
    
    // System Prompt Editing State
    const [isEditingPrompt, setIsEditingPrompt] = useState(false);
    const [promptValue, setPromptValue] = useState('');
    
    // Configuration Editing State
    const [isEditingConfig, setIsEditingConfig] = useState(false);
    const [configValues, setConfigValues] = useState({
        name: '',
        description: '',
        channel_secret: '',
        channel_access_token: '',
    });

    const { data: bot, isLoading } = useQuery<BotDetail>({
        queryKey: ['bot', botId],
        queryFn: async () => {
            const response = await api.get(`/bots/${botId}`);
            return response.data;
        },
        // Poll every 3 seconds if any file is not completed or failed
        refetchInterval: (query) => {
            const data = query.state.data;
            if (!data) return false;
            const hasPending = data.files.some((f: BotFile) => 
                f.status && !['completed', 'indexed', 'failed'].includes(f.status)
            );
            return hasPending ? 3000 : false;
        }
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

    const updateBotMutation = useMutation({
        mutationFn: async (data: { 
            name?: string;
            description?: string;
            channel_secret?: string;
            channel_access_token?: string;
            system_prompt?: string | null;
        }) => {
            await api.patch(`/bots/${botId}`, data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['bot', botId] });
            toast.success('Bot updated successfully');
            setIsEditingPrompt(false);
            setIsEditingConfig(false);
        },
        onError: () => {
            toast.error('Failed to update bot');
        },
    });

    const generatePromptMutation = useMutation({
        mutationFn: async () => {
             return await botApi.generatePrompt(botId);
        },
        onSuccess: (data) => {
             setPromptValue(data.suggested_prompt);
             setIsEditingPrompt(true);
             toast.success('System Prompt generated from Knowledge Base!');
        },
        onError: (error: any) => {
            console.error("AI Analysis Failed Detailed Error:", error);
            if (error.response) {
                console.error("Server Response:", error.response.data);
                console.error("Status Code:", error.response.status);
            }
            toast.error(error.response?.data?.detail || "AI Analysis failed");
        },
    });

    const handleStartEdit = () => {
        setPromptValue(bot?.system_prompt || '');
        setIsEditingPrompt(true);
    };

    const handleSavePrompt = () => {
        updateBotMutation.mutate({ system_prompt: promptValue || null });
    };

    const handleCancelEdit = () => {
        setIsEditingPrompt(false);
        setPromptValue('');
    };

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

            {/* Tab Navigation */}
            <div className="flex gap-2 border-b">
                <button
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'overview'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                    onClick={() => setActiveTab('overview')}
                >
                    <Settings className="h-4 w-4 inline-block mr-2" />
                    Overview
                </button>
                <button
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'files'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                    onClick={() => setActiveTab('files')}
                >
                    <FileIcon className="h-4 w-4 inline-block mr-2" />
                    Knowledge Base ({bot.file_count})
                </button>
                <button
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'logs'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                    onClick={() => setActiveTab('logs')}
                >
                    <ScrollText className="h-4 w-4 inline-block mr-2" />
                    Technical Logs
                </button>
                <button
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                        activeTab === 'chat'
                            ? 'border-primary text-primary'
                            : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                    onClick={() => setActiveTab('chat')}
                >
                    <Bot className="h-4 w-4 inline-block mr-2" />
                    Talk to Data
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
                <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle>Configuration</CardTitle>
                            {!isEditingConfig ? (
                                <Button variant="ghost" size="icon" onClick={() => {
                                    setConfigValues({
                                        name: bot.name || '',
                                        description: bot.description || '',
                                        channel_secret: '',
                                        channel_access_token: '',
                                    });
                                    setIsEditingConfig(true);
                                }}>
                                    <Pencil className="h-4 w-4" />
                                </Button>
                            ) : (
                                <div className="flex gap-2">
                                    <Button variant="ghost" size="icon" onClick={() => setIsEditingConfig(false)}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" onClick={() => {
                                        updateBotMutation.mutate({
                                            name: configValues.name || undefined,
                                            description: configValues.description || undefined,
                                            channel_secret: configValues.channel_secret || undefined,
                                            channel_access_token: configValues.channel_access_token || undefined,
                                        });
                                        setIsEditingConfig(false);
                                    }} disabled={updateBotMutation.isPending}>
                                        <Check className="h-4 w-4 text-green-500" />
                                    </Button>
                                </div>
                            )}
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {isEditingConfig ? (
                                <div className="space-y-4">
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground">Bot Name</label>
                                        <Input
                                            value={configValues.name}
                                            onChange={(e) => setConfigValues(prev => ({ ...prev, name: e.target.value }))}
                                            placeholder="Bot name"
                                            className="mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground">Description</label>
                                        <Textarea
                                            value={configValues.description}
                                            onChange={(e) => setConfigValues(prev => ({ ...prev, description: e.target.value }))}
                                            placeholder="Bot description..."
                                            className="mt-1 min-h-[60px]"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 text-sm border-t pt-4">
                                        <div className="font-medium text-muted-foreground">Bot ID</div>
                                        <div className="font-mono text-xs">{bot.id}</div>
                                        <div className="font-medium text-muted-foreground">Channel ID</div>
                                        <div className="font-mono">{bot.channel_id}</div>
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground">Channel Secret (leave empty to keep current)</label>
                                        <Input
                                            type="password"
                                            value={configValues.channel_secret}
                                            onChange={(e) => setConfigValues(prev => ({ ...prev, channel_secret: e.target.value }))}
                                            placeholder="••••••••"
                                            className="mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-medium text-muted-foreground">Channel Access Token (leave empty to keep current)</label>
                                        <Textarea
                                            value={configValues.channel_access_token}
                                            onChange={(e) => setConfigValues(prev => ({ ...prev, channel_access_token: e.target.value }))}
                                            placeholder="••••••••"
                                            className="mt-1 min-h-[60px]"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 text-sm border-t pt-4">
                                        <div className="font-medium text-muted-foreground">Webhook URL</div>
                                        <div className="font-mono text-xs break-all">{bot.webhook_url}</div>
                                        <div className="font-medium text-muted-foreground">Created</div>
                                        <div>{format(new Date(bot.created_at), 'PPP p')}</div>
                                        <div className="font-medium text-muted-foreground">Sessions</div>
                                        <div>{bot.session_count}</div>
                                        <div className="font-medium text-muted-foreground">Files</div>
                                        <div>{bot.file_count}</div>
                                    </div>
                                </div>
                            ) : (
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div className="font-medium text-muted-foreground">Bot Name</div>
                                    <div className="col-span-2 font-medium">{bot.name}</div>
                                    
                                    <div className="font-medium text-muted-foreground">Description</div>
                                    <div className="col-span-2 text-muted-foreground">{bot.description || 'No description'}</div>
                                    
                                    <div className="font-medium text-muted-foreground">Bot ID</div>
                                    <div className="col-span-2 font-mono text-xs">{bot.id}</div>
                                    
                                    <div className="font-medium text-muted-foreground">Channel ID</div>
                                    <div className="col-span-2 font-mono">{bot.channel_id}</div>
                                    
                                    <div className="font-medium text-muted-foreground">Channel Secret</div>
                                    <div className="col-span-2 font-mono">••••••••</div>
                                    
                                    <div className="font-medium text-muted-foreground">Access Token</div>
                                    <div className="col-span-2 font-mono">••••••••</div>
                                    
                                    <div className="font-medium text-muted-foreground">Webhook URL</div>
                                    <div className="col-span-2 font-mono text-xs break-all">{bot.webhook_url}</div>
                                    
                                    <div className="font-medium text-muted-foreground">Created</div>
                                    <div className="col-span-2">{format(new Date(bot.created_at), 'PPP p')}</div>

                                    <div className="font-medium text-muted-foreground">Sessions</div>
                                    <div className="col-span-2">{bot.session_count}</div>

                                    <div className="font-medium text-muted-foreground">Files</div>
                                    <div className="col-span-2">{bot.file_count}</div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <div className="space-y-1.5">
                                <CardTitle>Custom System Prompt</CardTitle>
                                <CardDescription>
                                    Override the default AI system prompt for this bot
                                </CardDescription>
                            </div>
                            {!isEditingPrompt ? (
                                <div className="flex gap-2">
                                     <Button 
                                        variant="outline" 
                                        size="sm" 
                                        className="gap-2 text-purple-400 border-purple-500/30 hover:bg-purple-500/10"
                                        onClick={() => generatePromptMutation.mutate()}
                                        disabled={generatePromptMutation.isPending}
                                     >
                                        <Wand2 className={`h-4 w-4 ${generatePromptMutation.isPending ? 'animate-spin' : ''}`} />
                                        {generatePromptMutation.isPending ? 'Generating...' : 'Auto-Generate'}
                                     </Button>
                                    <Button variant="ghost" size="icon" onClick={handleStartEdit}>
                                        <Pencil className="h-4 w-4" />
                                    </Button>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <Button variant="ghost" size="icon" onClick={handleCancelEdit}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                    <Button variant="ghost" size="icon" onClick={handleSavePrompt} disabled={updateBotMutation.isPending}>
                                        <Check className="h-4 w-4 text-green-500" />
                                    </Button>
                                </div>
                            )}
                        </CardHeader>
                        <CardContent>
                            {isEditingPrompt ? (
                                <div className="space-y-2">
                                    <Button
                                        onClick={() => {
                                            // Call generate API
                                            generatePromptMutation.mutate();
                                        }}
                                        disabled={generatePromptMutation.isPending}
                                        className="h-8 text-xs bg-[var(--gold)] hover:bg-[var(--gold-light)] text-black font-bold border-0"
                                    >
                                        {generatePromptMutation.isPending ? (
                                            <>
                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                                Generating...
                                            </>
                                        ) : (
                                            <>
                                                <Wand2 className="mr-2 h-3 w-3" />
                                                Auto-Generate from File Prompts
                                            </>
                                        )}
                                    </Button>
                                    <Textarea
                                        value={promptValue}
                                        onChange={(e) => setPromptValue(e.target.value)}
                                        className="min-h-[200px] font-mono text-sm"
                                        placeholder="Enter custom system prompt..."
                                    />
                                </div>
                            ) : (
                                bot.system_prompt ? (
                                    <div className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-96 prose prose-invert prose-sm prose-headings:text-purple-400 prose-strong:text-purple-300 prose-li:marker:text-purple-400">
                                        <ReactMarkdown>{bot.system_prompt}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <p className="text-sm text-muted-foreground italic">
                                        Using default system prompt configuration.
                                    </p>
                                )
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}

            {activeTab === 'files' && (
                <Card>
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
                            Upload text files (TXT, CSV, MD, PDF) to be used as knowledge base.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[250px]">Filename</TableHead>
                                    <TableHead className="w-[100px]">Status</TableHead>
                                    <TableHead>File Prompt / Context</TableHead>
                                    <TableHead className="w-[150px]">Uploaded</TableHead>
                                    <TableHead className="text-right w-[80px]">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {bot.files?.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                                            No files uploaded yet.
                                        </TableCell>
                                    </TableRow>
                                )}
                                {bot.files?.map((file) => (
                                    <FileTableRow 
                                        key={file.id} 
                                        file={file} 
                                        onDelete={(id) => setFileToDelete(id)} 
                                    />
                                ))}
                            </TableBody>
                        </Table>
                        </div>
                    </CardContent>
                </Card>
            )}

            {activeTab === 'logs' && (
                <BotLogViewer botId={botId} />
            )}

            {activeTab === 'chat' && (
                <TalkToData 
                    botId={botId} 
                    botName={bot.name}
                    systemPromptPreview={bot.system_prompt?.slice(0, 100)}
                    fileCount={bot.file_count}
                />
            )}

            <AlertDialog open={!!fileToDelete} onOpenChange={(open) => !open && setFileToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete this file?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently remove the file from the knowledge base.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => {
                                if (fileToDelete) {
                                    deleteFileMutation.mutate(fileToDelete);
                                    setFileToDelete(null);
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
