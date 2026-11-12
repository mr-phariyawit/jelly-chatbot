import { test, expect } from '@playwright/test';
import fs from 'fs';

// Target Production Backend API
const API_URL = 'https://session-api-m55puks34q-as.a.run.app';

test.describe('Bot Creation & Analysis Workflow', () => {
    let botId: string;
    let fileId: string;
    // Absolute path to the reference file
    const botTestFilePath = '/Users/mr.phariyawit/Documents/ai-support/bot-test.txt';

    test('should create bot from credentials and analyze file', async ({ request }) => {
        console.log('--- Starting Bot Creation Workflow ---');

        // 1. Create Bot via API
        const botPayload = {
            name: 'LINE Integration Test Bot',
            description: 'Bot created via Playwright using bot-test.txt credentials.',
            channel_id: process.env.E2E_LINE_CHANNEL_ID ?? 'test_channel_id',
            channel_secret: process.env.E2E_LINE_CHANNEL_SECRET ?? 'test_secret',
            user_id: process.env.E2E_LINE_USER_ID ?? 'U_TEST_USER',
            channel_access_token: process.env.E2E_LINE_CHANNEL_ACCESS_TOKEN ?? 'test_token',
            system_prompt: 'You are a test bot.'
        };

        const createRes = await request.post(`${API_URL}/bots`, {
            data: botPayload
        });

        // Debug response if failed
        if (!createRes.ok()) {
            console.error('Create Bot Failed:', await createRes.text());
        }
        expect(createRes.ok()).toBeTruthy();
        
        const botData = await createRes.json();
        botId = botData.id;
        console.log(`✅ Bot Created successfully. ID: ${botId}`);

        // 2. Upload the bot-test.txt file to this bot
        const fileBuffer = fs.readFileSync(botTestFilePath);
        
        const uploadRes = await request.post(`${API_URL}/bots/${botId}/files`, {
            multipart: {
                file: {
                    name: 'bot-test.txt',
                    mimeType: 'text/plain',
                    buffer: fileBuffer
                }
            }
        });

        if (!uploadRes.ok()) {
            console.error('Upload Failed:', await uploadRes.text());
        }
        expect(uploadRes.ok()).toBeTruthy();
        
        const fileData = await uploadRes.json();
        fileId = fileData.id;
        console.log(`✅ File Uploaded successfully. ID: ${fileId}`);

        // 3. Trigger AI Analysis
        console.log('Triggering AI Analysis...');
        const analyzeRes = await request.post(`${API_URL}/files/${fileId}/analyze`);
        
        if (!analyzeRes.ok()) {
             console.error('Analysis Failed:', await analyzeRes.text());
        }
        expect(analyzeRes.ok()).toBeTruthy();
        
        const analyzeData = await analyzeRes.json();
        console.log('✅ AI Analysis Result:', analyzeData);

        // Verify that analysis description was generated
        expect(analyzeData).toHaveProperty('summary');
        expect(analyzeData.summary.length).toBeGreaterThan(0);
        
        console.log('--- Workflow Complete ---');
    });
});
