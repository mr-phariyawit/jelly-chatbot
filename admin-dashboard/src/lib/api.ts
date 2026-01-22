import axios from 'axios';

// Default to production, can be overridden by env var
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://session-api-n7u6wpcbqa-uc.a.run.app";

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface Bot {
    id: string;
    name: string;
    description?: string;
    channel_id: string;
    webhook_path: string;
    webhook_url: string;
    is_active: boolean;
    file_count: number;
    session_count: number;
    created_at: string;
    system_prompt?: string;
    model_config_json?: string;
    trigger_names?: string[] | null;
}

export interface BotDetail extends Bot {
    files: BotFile[];
}

export interface BotFile {
    id: string;
    bot_id: string;
    filename: string;
    content_type?: string;
    size_bytes?: number;
    uploaded_at: string;
    description?: string;
    status?: 'pending' | 'processing' | 'extracted' | 'indexing' | 'indexed' | 'completed' | 'failed';
    indexing_progress?: number;
}

export interface Session {
    id: string;
    user_id: string;
    bot_id?: string;
    started_at: string;
    ended_at?: string;
    status: string;
    is_escalated: boolean;
    escalation_reason?: string;
    message_count: number;
}

export interface Message {
    id: string;
    session_id: string;
    role: string;
    content: string;
    timestamp: string;
}

export interface SessionDetail extends Session {
    messages: Message[];
}

export interface AdminUser {
    id: string;
    email: string;
    name?: string;
    avatar_url?: string;
    role: string;
    is_approved: boolean;
    allowed_bot_ids?: string[];
    created_at?: string;
    last_login?: string;
}

// BotLog types
export interface BotLog {
    id: string;
    bot_id: string;
    level: 'INFO' | 'WARN' | 'ERROR';
    event_type: 'WEBHOOK' | 'LLM_CALL' | 'RAG_SEARCH' | 'JIRA' | 'ERROR';
    message: string;
    metadata?: string; // JSON string
    created_at: string;
}

export interface BotLogsResponse {
    logs: BotLog[];
    total: number;
    page: number;
    page_size: number;
}

export interface BotLogStats {
    total: number;
    by_level: {
        INFO: number;
        WARN: number;
        ERROR: number;
    };
    by_event_type: {
        WEBHOOK: number;
        LLM_CALL: number;
        RAG_SEARCH: number;
        JIRA: number;
    };
}

// Auth API functions
export const authApi = {
    googleAuth: async (data: {
        email: string;
        name?: string;
        avatar_url?: string;
        google_id: string;
    }) => {
        const response = await api.post<AdminUser>('/auth/google', data);
        return response.data;
    },

    getCurrentUser: async (email: string) => {
        const response = await api.get<AdminUser>('/auth/me', {
            params: { email },
        });
        return response.data;
    },

    listUsers: async () => {
        const response = await api.get<AdminUser[]>('/users');
        return response.data;
    },

    updateUser: async (userId: string, data: {
        name?: string;
        role?: string;
        allowed_bot_ids?: string[];
    }) => {
        const response = await api.put<AdminUser>(`/users/${userId}`, data);
        return response.data;
    },

    deleteUser: async (userId: string) => {
        const response = await api.delete(`/users/${userId}`);
        return response.data;
    },
};

// Bot Logs API functions
export const botLogsApi = {
    getLogs: async (botId: string, params?: {
        level?: string;
        event_type?: string;
        page?: number;
        page_size?: number;
    }) => {
        const response = await api.get<BotLogsResponse>(`/bots/${botId}/logs`, { params });
        return response.data;
    },

    getLogDetail: async (botId: string, logId: string) => {
        const response = await api.get<BotLog>(`/bots/${botId}/logs/${logId}`);
        return response.data;
    },

    getLogStats: async (botId: string) => {
        const response = await api.get<BotLogStats>(`/bots/${botId}/logs/stats`);
        return response.data;
    },

    clearLogs: async (botId: string, olderThanDays: number = 7) => {
        const response = await api.delete(`/bots/${botId}/logs`, {
            params: { older_than_days: olderThanDays },
        });
        return response.data;
    },
};

// Bot API functions
export const botApi = {
    updateBot: async (botId: string, data: {
        name?: string;
        description?: string;
        channel_secret?: string;
        channel_access_token?: string;
        is_active?: boolean;
        system_prompt?: string;
        model_config_json?: string;
        trigger_names?: string[] | null;
    }) => {
        const response = await api.patch<Bot>(`/bots/${botId}`, data);
        return response.data;
    },

    generatePrompt: async (botId: string) => {
        const response = await api.post<{ suggested_prompt: string }>(`/bots/${botId}/generate-prompt`);
        return response.data;
    },
};

export const fileApi = {
    updateFile: async (fileId: string, data: { description?: string }) => {
        const response = await api.patch<BotFile>(`/files/${fileId}`, data);
        return response.data;
    },

    analyzeFile: async (fileId: string) => {
        const response = await api.post<{ summary: string }>(`/files/${fileId}/analyze`);
        return response.data;
    },

    uploadFileWithSignedUrl: async (botId: string, file: File) => {
        // 1. Get Session URI (Resumable Upload URL)
        const { data: signed } = await api.post<{ upload_url: string; gcs_uri: string; file_id: string }>(
            `/bots/${botId}/files/signed-url`,
            { filename: file.name, content_type: file.type || 'application/octet-stream' }
        );

        // 2. Upload to GCS with retry logic using native fetch (bypasses any axios defaults)
        const MAX_RETRIES = 3;
        let lastError: Error | null = null;

        for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                // Use native fetch to ensure no extra headers are added
                const uploadResponse = await fetch(signed.upload_url, {
                    method: 'PUT',
                    headers: { 'Content-Type': file.type || 'application/octet-stream' },
                    body: file,
                });

                if (!uploadResponse.ok) {
                    throw new Error(`Upload failed with status ${uploadResponse.status}`);
                }

                lastError = null;
                break; // Success, exit retry loop
            } catch (error) {
                lastError = error as Error;
                console.error(`[Upload] Error on attempt ${attempt}/${MAX_RETRIES}:`, error);

                if (attempt === MAX_RETRIES) {
                    // Check if it's likely a CORS error (TypeError: Failed to fetch)
                    if (error instanceof TypeError && (error as TypeError).message.includes('fetch')) {
                        throw new Error('Upload blocked by browser security (CORS). Please contact support.');
                    }
                    throw error;
                }

                // Wait before retry (exponential backoff: 1s, 2s, 4s)
                await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
            }
        }

        if (lastError) {
            throw lastError;
        }

        // 3. Confirm upload
        const response = await api.post<BotFile>(`/bots/${botId}/files/confirm`, {
            file_id: signed.file_id,
            gcs_uri: signed.gcs_uri,
            filename: file.name,
            content_type: file.type || 'application/octet-stream',
            size_bytes: file.size
        });

        return response.data;
    },
};

// Upload Progress Types
export interface UploadProgress {
    loaded: number;      // bytes uploaded
    total: number;       // total file size
    percent: number;     // 0-100
    speed: number;       // bytes/sec
    eta: number;         // seconds remaining
    filename: string;
}

export interface UploadController {
    abort: () => void;
}

/**
 * Upload file with real-time progress tracking
 * Uses XMLHttpRequest for progress events (fetch doesn't support upload progress)
 */
export const uploadFileWithProgress = async (
    botId: string,
    file: File,
    onProgress: (progress: UploadProgress) => void,
): Promise<{ data: BotFile; controller: UploadController }> => {
    // 1. Get Session URI (Resumable Upload URL)
    const { data: signed } = await api.post<{ upload_url: string; gcs_uri: string; file_id: string }>(
        `/bots/${botId}/files/signed-url`,
        { filename: file.name, content_type: file.type || 'application/octet-stream' }
    );

    // 2. Upload to GCS with XMLHttpRequest for progress tracking
    const xhr = new XMLHttpRequest();
    const startTime = Date.now();
    let aborted = false;

    const controller: UploadController = {
        abort: () => {
            aborted = true;
            xhr.abort();
        }
    };

    await new Promise<void>((resolve, reject) => {
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const elapsed = (Date.now() - startTime) / 1000;
                const speed = elapsed > 0 ? e.loaded / elapsed : 0;
                const eta = speed > 0 ? (e.total - e.loaded) / speed : 0;

                onProgress({
                    loaded: e.loaded,
                    total: e.total,
                    percent,
                    speed,
                    eta,
                    filename: file.name,
                });
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve();
            } else {
                reject(new Error(`Upload failed with status ${xhr.status}`));
            }
        };

        xhr.onerror = () => {
            if (aborted) {
                reject(new Error('Upload cancelled'));
            } else {
                reject(new Error('Upload blocked by browser security (CORS). Please contact support.'));
            }
        };

        xhr.onabort = () => {
            reject(new Error('Upload cancelled'));
        };

        xhr.open('PUT', signed.upload_url);
        xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
        xhr.send(file);
    });

    // 3. Confirm upload
    const response = await api.post<BotFile>(`/bots/${botId}/files/confirm`, {
        file_id: signed.file_id,
        gcs_uri: signed.gcs_uri,
        filename: file.name,
        content_type: file.type || 'application/octet-stream',
        size_bytes: file.size
    });

    return { data: response.data, controller };
};
