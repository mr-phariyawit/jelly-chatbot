/**
 * Session API Client
 * 
 * Calls the Session Logging API to track chat sessions
 */

const SESSION_API_URL = 'https://session-api-1088865818405.us-central1.run.app';

export interface AddMessageResult {
    session_id: string;
    message_id: string;
    is_new_session: boolean;
}

/**
 * Add a message to the session log.
 * Creates new session if none exists or if last message > 30 min ago.
 */
export async function logMessage(
    userId: string,
    role: 'user' | 'assistant',
    content: string,
    isEscalated: boolean = false,
    escalationReason?: string
): Promise<AddMessageResult | null> {
    try {
        const response = await fetch(`${SESSION_API_URL}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                role: role,
                content: content,
                is_escalated: isEscalated,
                escalation_reason: escalationReason,
            }),
        });

        if (!response.ok) {
            console.error('Session API error:', response.status, await response.text());
            return null;
        }

        return await response.json() as AddMessageResult;
    } catch (error) {
        console.error('Error calling Session API:', error);
        return null;
    }
}

/**
 * Log a user message to the session.
 */
export async function logUserMessage(userId: string, content: string): Promise<AddMessageResult | null> {
    return logMessage(userId, 'user', content);
}

/**
 * Log an assistant message to the session.
 */
export async function logAssistantMessage(
    userId: string,
    content: string,
    isEscalated: boolean = false,
    escalationReason?: string
): Promise<AddMessageResult | null> {
    return logMessage(userId, 'assistant', content, isEscalated, escalationReason);
}
