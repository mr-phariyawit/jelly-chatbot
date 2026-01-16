import axios from 'axios';

// Default to production, can be overridden by env var
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://session-api-n7u6wpcbqa-uc.a.run.app';

export const api = axios.create({
    baseURL: BASE_URL,
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
};

