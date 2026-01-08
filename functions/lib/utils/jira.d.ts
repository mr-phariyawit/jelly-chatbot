/**
 * JIRA Integration Utilities
 *
 * Create and manage JIRA tickets for IT Support escalation
 * Updated: 2026-01-07T20:52:30 - Using JIRA_API_TOKEN v3 only
 */
interface IncidentData {
    summary: string;
    description: string;
    system: string;
    category: string;
    priority?: 'very_low' | 'low' | 'medium' | 'high';
}
interface JiraTicket {
    key: string;
    id: string;
    self: string;
}
/**
 * Create a JIRA ticket for escalation
 */
export declare function createJiraTicket(incident: IncidentData): Promise<JiraTicket | null>;
/**
 * Add comment to existing JIRA ticket
 */
export declare function addJiraComment(issueKey: string, comment: string): Promise<boolean>;
/**
 * Get JIRA ticket status
 */
export declare function getJiraTicketStatus(issueKey: string): Promise<string | null>;
export {};
//# sourceMappingURL=jira.d.ts.map