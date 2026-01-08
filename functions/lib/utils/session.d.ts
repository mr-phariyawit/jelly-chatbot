/**
 * Session API Client
 *
 * Calls the Session Logging API to track chat sessions
 */
export interface AddMessageResult {
    session_id: string;
    message_id: string;
    is_new_session: boolean;
}
/**
 * Add a message to the session log.
 * Creates new session if none exists or if last message > 30 min ago.
 */
export declare function logMessage(userId: string, role: 'user' | 'assistant', content: string, isEscalated?: boolean, escalationReason?: string): Promise<AddMessageResult | null>;
/**
 * Log a user message to the session.
 */
export declare function logUserMessage(userId: string, content: string): Promise<AddMessageResult | null>;
/**
 * Log an assistant message to the session.
 */
export declare function logAssistantMessage(userId: string, content: string, isEscalated?: boolean, escalationReason?: string): Promise<AddMessageResult | null>;
//# sourceMappingURL=session.d.ts.map