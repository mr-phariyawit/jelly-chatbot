/**
 * IT Support Message Processor
 *
 * Main logic for processing support requests using AI (Gemini)
 */
interface MessageInput {
    userId: string;
    messageType: 'text' | 'image';
    content: string;
    imageUrl?: string;
}
interface MessageOutput {
    message: string;
    shouldEscalate: boolean;
    incidentId?: string;
    jiraTicketKey?: string;
}
/**
 * Process IT support message with AI
 */
export declare function processITSupportMessage(input: MessageInput): Promise<MessageOutput>;
export { processITSupportMessage as processMessage };
//# sourceMappingURL=processor.d.ts.map