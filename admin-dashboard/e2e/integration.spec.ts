import { test, expect } from '@playwright/test';

const TARGET_URL = process.env.TARGET_URL || 'https://admin-dashboard-687023036300.us-central1.run.app';

test.describe('Bot Integration Flow', () => {
    test('should create bot, receive webhook, and log session', async ({ page }) => {
        // 1. Create a new Bot
        await page.goto(`${TARGET_URL}/admin/bots`);
        await page.getByRole('button', { name: 'Create Bot' }).click();

        const botName = `Auto Test Bot ${Date.now()}`;
        await page.getByLabel('Bot Name').fill(botName);
        await page.getByLabel('Channel ID').fill('1234567890');
        await page.getByLabel('Channel Secret').fill('test_secret');
        await page.getByLabel('Channel Access Token').fill('test_token');

        // Monitor network response
        const [createBotResponse] = await Promise.all([
            page.waitForResponse(resp => resp.url().includes('/bots') && resp.request().method() === 'POST'),
            page.getByRole('button', { name: 'Create Bot' }).click()
        ]);

        console.log(`Create Bot Status: ${createBotResponse.status()}`);
        console.log(`Create Bot Body: ${await createBotResponse.text()}`);

        expect(createBotResponse.status()).toBe(200);
        const createdBot = await createBotResponse.json();
        const botId = createdBot.id;

        // Wait for creation and dialog close
        await expect(page.getByRole('dialog')).not.toBeVisible();
        console.log(`Created Bot ID: ${botId}`);

        // 3. Construct Webhook URL
        const apiBaseUrl = 'https://session-api-687023036300.us-central1.run.app';
        const webhookUrl = `${apiBaseUrl}/webhook/${botId.substring(0, 8)}`;
        console.log(`Testing Webhook URL: ${webhookUrl}`);

        // 4. Simulate LINE Webhook Event
        const userId = `U_e2e_${Date.now()}`;
        const webhookPayload = {
            destination: "U1234567890",
            events: [
                {
                    type: "message",
                    message: {
                        type: "text",
                        id: "325708",
                        text: "Hello Cloud SQL!"
                    },
                    timestamp: Date.now(),
                    source: {
                        type: "user",
                        userId: userId
                    },
                    replyToken: "7f76ed0d593b46d093285c06981186f4",
                    mode: "active"
                }
            ]
        };

        console.log('Sending Webhook...');
        // Use page.request directly, it is already a context
        const webhookResponse = await page.request.post(webhookUrl, {
            data: webhookPayload
        });

        console.log(`Webhook Status: ${webhookResponse.status()}`);
        expect(webhookResponse.status()).toBe(200);

        // 5. Verify Session Logged (Real Persistence)
        await page.goto(`${TARGET_URL}/admin/sessions`);

        // Poll for session existence (it might take a second to persist/index)
        await expect(async () => {
            await page.reload();
            await expect(page.getByText(userId)).toBeVisible();
        }).toPass({ timeout: 30000 });

        console.log('Session verified in dashboard! Persistence works!');
    });
});
