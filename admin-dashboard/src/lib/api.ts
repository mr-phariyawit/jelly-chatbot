import axios from 'axios';

// Default to local development, can be overridden by env var
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://session-api-687023036300.us-central1.run.app';

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
