"use strict";
/**
 * Session API Client
 *
 * Calls the Session Logging API to track chat sessions
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.logMessage = logMessage;
exports.logUserMessage = logUserMessage;
exports.logAssistantMessage = logAssistantMessage;
const SESSION_API_URL = 'https://session-api-687023036300.us-central1.run.app';
/**
 * Add a message to the session log.
 * Creates new session if none exists or if last message > 30 min ago.
 */
async function logMessage(userId, role, content, isEscalated = false, escalationReason) {
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
        return await response.json();
    }
    catch (error) {
        console.error('Error calling Session API:', error);
        return null;
    }
}
/**
 * Log a user message to the session.
 */
async function logUserMessage(userId, content) {
    return logMessage(userId, 'user', content);
}
/**
 * Log an assistant message to the session.
 */
async function logAssistantMessage(userId, content, isEscalated = false, escalationReason) {
    return logMessage(userId, 'assistant', content, isEscalated, escalationReason);
}
//# sourceMappingURL=session.js.map