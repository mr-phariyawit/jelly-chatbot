
import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Target Production Backend API
const API_URL = 'https://session-api-m55puks34q-as.a.run.app';

test.describe('Backend API Analysis Verification', () => {
    let botId: string;
    let fileId: string;

    // Create a dummy file for testing
    const testFilePath = path.join(__dirname, 'api-test-doc.txt');
    
    test.beforeAll(async () => {
        fs.writeFileSync(testFilePath, 'This is a test document about Project Orion. Key features include Warp Drive and Shield Generators. Use this for testing AI analysis.');
    });

    test.afterAll(async () => {
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
    });

    test('should creation session, upload file, and auto-analyze', async ({ request }) => {
        // 1. Create Default Bot (or get existing)
        const botRes = await request.post(`${API_URL}/bots/create-default`);
        expect(botRes.ok()).toBeTruthy();
        const botData = await botRes.json();
        botId = botData.id;
        console.log(`Using Bot ID: ${botId}`);

        // 2. Upload File
        // Playwright handles multipart when passing Object with 'file' key pointing to file stream/buffer or path
        const fileBuffer = fs.readFileSync(testFilePath);
        
        const uploadRes = await request.post(`${API_URL}/bots/${botId}/files`, {
            multipart: {
                file: {
                    name: 'api-test-doc.txt',
                    mimeType: 'text/plain',
                    buffer: fileBuffer
                }
            }
        });
        
        expect(uploadRes.ok()).toBeTruthy();
        const fileData = await uploadRes.json();
        fileId = fileData.id;
        console.log(`Uploaded File ID: ${fileId}`);

        // 3. Trigger AI Analysis
        // This was failing with 403 or Error before
        const analyzeRes = await request.post(`${API_URL}/files/${fileId}/analyze`);
        
        // Assertions
        expect(analyzeRes.ok()).toBeTruthy(); // Should be 200 OK now
        const analyzeData = await analyzeRes.json();
        
        console.log('AI Analysis Result:', analyzeData);
        
        // Verify Content
        expect(analyzeData).toHaveProperty('summary');
        expect(analyzeData.summary).not.toContain('Error');
        expect(analyzeData.summary.length).toBeGreaterThan(10);
    });
});
