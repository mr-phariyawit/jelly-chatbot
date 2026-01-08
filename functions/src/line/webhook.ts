/**
 * LINE Webhook Handler
 * 
 * Receives webhook events from LINE Platform and processes them
 */

import { onRequest } from 'firebase-functions/v2/https';
import { defineSecret } from 'firebase-functions/params';
import * as line from '@line/bot-sdk';
import { processITSupportMessage } from '../support/processor';

// Define secrets for LINE credentials
const lineChannelSecret = defineSecret('LINE_CHANNEL_SECRET');
const lineChannelAccessToken = defineSecret('LINE_CHANNEL_ACCESS_TOKEN');

// LINE Client configuration
function getLineClient(): line.messagingApi.MessagingApiClient {
    return new line.messagingApi.MessagingApiClient({
        channelAccessToken: lineChannelAccessToken.value(),
    });
}

/**
 * Validate LINE webhook signature using official SDK
 */
function validateLineSignature(body: Buffer, signature: string, secret: string): boolean {
    return line.validateSignature(body, secret, signature);
}

// Define Gemini API Key secret
const geminiApiKey = defineSecret('GEMINI_API_KEY');

// Define JIRA secrets
const jiraApiToken = defineSecret('JIRA_API_TOKEN');
const jiraEmail = defineSecret('JIRA_EMAIL');

/**
 * Main LINE webhook handler
 */
export const lineWebhook = onRequest(
    {
        secrets: [lineChannelSecret, lineChannelAccessToken, geminiApiKey, jiraApiToken, jiraEmail],
        cors: false,
    },
    async (req, res) => {
        // Only accept POST requests
        if (req.method !== 'POST') {
            res.status(405).send('Method Not Allowed');
            return;
        }

        // Validate signature
        const signature = req.headers['x-line-signature'] as string;
        if (!signature) {
            console.warn('Missing LINE signature');
            res.status(400).send('Missing signature');
            return;
        }

        // Use rawBody for accurate signature validation
        // Firebase Cloud Functions provides rawBody as Buffer
        const rawBody = (req as any).rawBody as Buffer;
        if (!rawBody) {
            console.warn('Missing rawBody');
            res.status(400).send('Missing body');
            return;
        }

        // Debug: log secret and signature info
        const secret = lineChannelSecret.value();
        console.log('Debug: secret length:', secret?.length, 'signature:', signature?.substring(0, 20) + '...');
        console.log('Debug: rawBody length:', rawBody?.length);

        if (!validateLineSignature(rawBody, signature, secret)) {
            console.warn('Invalid LINE signature');
            res.status(401).send('Invalid signature');
            return;
        }

        // Process events
        const events: line.WebhookEvent[] = req.body.events;
        const client = getLineClient();

        try {
            await Promise.all(
                events.map(async (event) => {
                    console.log('Received event:', JSON.stringify(event));

                    if (event.type === 'message' && event.replyToken) {
                        // Handle message events
                        const response = await handleMessageEvent(event, client);

                        if (response) {
                            await client.replyMessage({
                                replyToken: event.replyToken,
                                messages: response,
                            });
                        }
                    }
                })
            );

            res.status(200).send('OK');
        } catch (error) {
            console.error('Error processing webhook:', error);
            res.status(500).send('Internal Server Error');
        }
    }
);

/**
 * Handle LINE message events
 */
async function handleMessageEvent(
    event: line.MessageEvent,
    _client: line.messagingApi.MessagingApiClient
): Promise<line.messagingApi.Message[] | null> {
    const userId = event.source.userId;

    if (!userId) {
        return null;
    }

    // Handle different message types
    switch (event.message.type) {
        case 'text':
            return handleTextMessage(event.message.text, userId);

        case 'image':
            return handleImageMessage(event.message.id, userId);

        default:
            return [{
                type: 'text',
                text: 'ขออภัยค่ะ ขณะนี้รองรับเฉพาะข้อความและรูปภาพเท่านั้น',
            }];
    }
}

/**
 * Handle text messages
 */
async function handleTextMessage(
    text: string,
    userId: string
): Promise<line.messagingApi.Message[]> {
    try {
        // Process with AI
        const response = await processITSupportMessage({
            userId,
            messageType: 'text',
            content: text,
        });

        return [{
            type: 'text',
            text: response.message,
        }];
    } catch (error) {
        console.error('Error processing text message:', error);
        return [{
            type: 'text',
            text: 'ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง',
        }];
    }
}

/**
 * Handle image messages
 */
async function handleImageMessage(
    _messageId: string,
    userId: string
): Promise<line.messagingApi.Message[]> {
    try {
        // TODO: Implement image analysis
        // 1. Download image from LINE
        // 2. Upload to Cloud Storage
        // 3. Analyze with Gemini Vision

        const response = await processITSupportMessage({
            userId,
            messageType: 'image',
            content: '[รูปภาพ]',
            // imageUrl: cloudStorageUrl,
        });

        return [{
            type: 'text',
            text: response.message,
        }];
    } catch (error) {
        console.error('Error processing image message:', error);
        return [{
            type: 'text',
            text: 'ขออภัยค่ะ ไม่สามารถวิเคราะห์รูปภาพได้ กรุณาอธิบายปัญหาเป็นข้อความ',
        }];
    }
}
