import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

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
            description: 'Bot created via Playwright using bot-test.txt credentials. Basic ID: @073upziw',
            channel_id: '2008690282',
            channel_secret: 'd0bcaa5333ac29f1b65b0a204268fe8a',
            user_id: 'U4bc18b6ecbdc3f7984b2e249d16c854f',
            channel_access_token: '0CTKYq9cLZJJIQJRufb1ozz52/njox/wjMHbT8JDMdzi6Xe2GtkUSmGRCxQKfHxS4aUs2xodx+eNWTanqhcMV3Ptd2TuNCahyUnEREagEU6C4Ti/BEDqVnca/sLiDvNdoSrlmgH5Hsq5t/l+dIXDWwdB04t89/1O/w1cDnyilFU=',
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
