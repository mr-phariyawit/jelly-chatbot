"use strict";
/**
 * JIRA Integration Utilities
 *
 * Create and manage JIRA tickets for IT Support escalation
 * Updated: 2026-01-07T20:52:30 - Using JIRA_API_TOKEN v3 only
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createJiraTicket = createJiraTicket;
exports.addJiraComment = addJiraComment;
exports.getJiraTicketStatus = getJiraTicketStatus;
const jira_js_1 = require("jira.js");
const params_1 = require("firebase-functions/params");
// JIRA credentials
const jiraApiToken = (0, params_1.defineSecret)('JIRA_API_TOKEN');
const jiraEmail = (0, params_1.defineSecret)('JIRA_EMAIL');
// JIRA configuration
const JIRA_HOST = 'jventures.atlassian.net';
const JIRA_PROJECT_KEY = 'CS'; // Customer Support project
/**
 * Map internal priority to JIRA priority
 */
function mapPriority(priority) {
    switch (priority) {
        case 'high':
            return 'High';
        case 'medium':
            return 'Medium';
        case 'low':
            return 'Low';
        case 'very_low':
            return 'Lowest';
        default:
            return 'Medium';
    }
}
/**
 * Get JIRA client
 */
function getJiraClient() {
    return new jira_js_1.Version3Client({
        host: `https://${JIRA_HOST}`,
        authentication: {
            basic: {
                email: jiraEmail.value(),
                apiToken: jiraApiToken.value(),
            },
        },
    });
}
/**
 * Create a JIRA ticket for escalation
 */
async function createJiraTicket(incident) {
    try {
        console.log('JIRA: Starting ticket creation for:', incident.summary);
        console.log('JIRA: Email:', jiraEmail.value().substring(0, 5) + '...');
        console.log('JIRA: Token length:', jiraApiToken.value().length);
        const jira = getJiraClient();
        const issue = await jira.issues.createIssue({
            fields: {
                project: {
                    key: JIRA_PROJECT_KEY,
                },
                issuetype: {
                    name: 'Task',
                },
                summary: incident.summary,
                description: {
                    type: 'doc',
                    version: 1,
                    content: [
                        {
                            type: 'paragraph',
                            content: [
                                {
                                    type: 'text',
                                    text: incident.description,
                                },
                            ],
                        },
                    ],
                },
                priority: {
                    name: mapPriority(incident.priority),
                },
                labels: ['from-line-bot', incident.system, incident.category],
            },
        });
        console.log('Created JIRA ticket:', issue.key);
        return {
            key: issue.key,
            id: issue.id,
            self: issue.self,
        };
    }
    catch (error) {
        console.error('Error creating JIRA ticket:', error);
        return null;
    }
}
/**
 * Add comment to existing JIRA ticket
 */
async function addJiraComment(issueKey, comment) {
    try {
        const jira = getJiraClient();
        // Using any type to bypass strict typing issues with jira.js SDK
        await jira.issueComments.addComment({
            issueIdOrKey: issueKey,
            body: {
                type: 'doc',
                version: 1,
                content: [
                    {
                        type: 'paragraph',
                        content: [
                            {
                                type: 'text',
                                text: comment,
                            },
                        ],
                    },
                ],
            },
        });
        return true;
    }
    catch (error) {
        console.error('Error adding JIRA comment:', error);
        return false;
    }
}
/**
 * Get JIRA ticket status
 */
async function getJiraTicketStatus(issueKey) {
    try {
        const jira = getJiraClient();
        const issue = await jira.issues.getIssue({
            issueIdOrKey: issueKey,
            fields: ['status'],
        });
        return issue.fields?.status?.name || null;
    }
    catch (error) {
        console.error('Error getting JIRA ticket status:', error);
        return null;
    }
}
//# sourceMappingURL=jira.js.map