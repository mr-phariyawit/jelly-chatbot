"use strict";
/**
 * LINE Webhook Handler
 *
 * Receives webhook events from LINE Platform and processes them
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.lineWebhook = void 0;
const https_1 = require("firebase-functions/v2/https");
const params_1 = require("firebase-functions/params");
const line = __importStar(require("@line/bot-sdk"));
const processor_1 = require("../support/processor");
// Define secrets for LINE credentials
const lineChannelSecret = (0, params_1.defineSecret)('LINE_CHANNEL_SECRET');
const lineChannelAccessToken = (0, params_1.defineSecret)('LINE_CHANNEL_ACCESS_TOKEN');
// LINE Client configuration
function getLineClient() {
    return new line.messagingApi.MessagingApiClient({
        channelAccessToken: lineChannelAccessToken.value(),
    });
}
/**
 * Validate LINE webhook signature using official SDK
 */
function validateLineSignature(body, signature, secret) {
    return line.validateSignature(body, secret, signature);
}
// Define Gemini API Key secret
const geminiApiKey = (0, params_1.defineSecret)('GEMINI_API_KEY');
// Define JIRA secrets
const jiraApiToken = (0, params_1.defineSecret)('JIRA_API_TOKEN');
const jiraEmail = (0, params_1.defineSecret)('JIRA_EMAIL');
/**
 * Main LINE webhook handler
 */
exports.lineWebhook = (0, https_1.onRequest)({
    secrets: [lineChannelSecret, lineChannelAccessToken, geminiApiKey, jiraApiToken, jiraEmail],
    cors: false,
}, async (req, res) => {
    // Only accept POST requests
    if (req.method !== 'POST') {
        res.status(405).send('Method Not Allowed');
        return;
    }
    // Validate signature
    const signature = req.headers['x-line-signature'];
    if (!signature) {
        console.warn('Missing LINE signature');
        res.status(400).send('Missing signature');
        return;
    }
    // Use rawBody for accurate signature validation
    // Firebase Cloud Functions provides rawBody as Buffer
    const rawBody = req.rawBody;
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
    const events = req.body.events;
    const client = getLineClient();
    try {
        await Promise.all(events.map(async (event) => {
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
        }));
        res.status(200).send('OK');
    }
    catch (error) {
        console.error('Error processing webhook:', error);
        res.status(500).send('Internal Server Error');
    }
});
/**
 * Handle LINE message events
 */
async function handleMessageEvent(event, _client) {
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
async function handleTextMessage(text, userId) {
    try {
        // Process with AI
        const response = await (0, processor_1.processITSupportMessage)({
            userId,
            messageType: 'text',
            content: text,
        });
        return [{
                type: 'text',
                text: response.message,
            }];
    }
    catch (error) {
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
async function handleImageMessage(_messageId, userId) {
    try {
        // TODO: Implement image analysis
        // 1. Download image from LINE
        // 2. Upload to Cloud Storage
        // 3. Analyze with Gemini Vision
        const response = await (0, processor_1.processITSupportMessage)({
            userId,
            messageType: 'image',
            content: '[รูปภาพ]',
            // imageUrl: cloudStorageUrl,
        });
        return [{
                type: 'text',
                text: response.message,
            }];
    }
    catch (error) {
        console.error('Error processing image message:', error);
        return [{
                type: 'text',
                text: 'ขออภัยค่ะ ไม่สามารถวิเคราะห์รูปภาพได้ กรุณาอธิบายปัญหาเป็นข้อความ',
            }];
    }
}
//# sourceMappingURL=webhook.js.map