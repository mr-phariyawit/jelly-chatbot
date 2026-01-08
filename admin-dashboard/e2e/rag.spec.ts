
import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const BASE_URL = 'http://localhost:3000';

test.describe('RAG Knowledge Base Flow', () => {

    // Create a dummy file for upload
    const testFilePath = path.join(__dirname, 'test-knowledge.txt');

    test.beforeAll(() => {
        fs.writeFileSync(testFilePath, 'This is a test knowledge base file for Playwright.');
    });

    test.afterAll(() => {
        if (fs.existsSync(testFilePath)) {
            fs.unlinkSync(testFilePath);
        }
    });

    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
    });

    test('should create a bot and upload a knowledge file', async ({ page }) => {
        // 1. Navigate to Bots page
        await page.goto(`${BASE_URL}/admin/bots`);

        // Wait for loading to finish
        await expect(page.getByText('Loading bots...')).not.toBeVisible({ timeout: 10000 });

        await expect(page.getByRole('heading', { name: 'Bots' })).toBeVisible();

        // 2. Create a new Bot
        await page.getByRole('button', { name: 'Create Bot' }).click();
        await expect(page.getByRole('dialog')).toBeVisible();

        const timestamp = Date.now();
        const botName = `Playwright Bot ${timestamp}`;

        await page.getByLabel('Name').fill(botName);
        await page.getByLabel('Description').fill('Created by E2E Test');
        await page.getByLabel('Channel ID').fill(`123456${timestamp}`);
        await page.getByLabel('Channel Secret').fill('test_secret');
        await page.getByLabel('Channel Access Token').fill('test_token');

        // Wait for the modal submit and click
        await page.getByRole('button', { name: 'Create Bot', exact: true }).click();

        // Wait for success toast
        await expect(page.getByText('Bot created successfully')).toBeVisible();

        // Reload to ensure list update
        await page.reload();
        await expect(page.getByText('Loading bots...')).not.toBeVisible({ timeout: 10000 });

        // 3. Verify Bot Created
        // Increase timeout for list refresh
        await expect(page.getByText(botName)).toBeVisible({ timeout: 10000 });

        // Click on the bot to go to details (Click "Manage Files" button in the card)
        await page.locator('.space-y-6 .grid .rounded-xl') // Simple selector for Card
            .filter({ hasText: botName })
            .getByRole('link', { name: 'Manage Files' })
            .click();

        // Wait for navigation
        await expect(page).toHaveURL(/.*\/admin\/bots\/.+/);

        // Wait for details loading
        await expect(page.getByText('Loading bot details...')).not.toBeVisible({ timeout: 10000 });

        // 4. Verify Details Page
        // Use locator instead of role if role is flaky, but h2 should work.
        await expect(page.locator('h2').filter({ hasText: botName })).toBeVisible();
        await expect(page.getByText('Knowledge Base Files')).toBeVisible();

        // 5. Upload File
        // Note: The input is hidden, so we target by selector or label logic
        const fileInput = page.locator('input#file-upload');
        await fileInput.setInputFiles(testFilePath);

        // 6. Verify Upload Success
        // Wait for the file name to appear in the table
        await expect(page.getByRole('cell', { name: 'test-knowledge.txt' })).toBeVisible({ timeout: 10000 });

        // 7. Clean up (Delete File)
        // Find the row with the file and click delete
        // Note: We need to handle the window.confirm dialog
        page.on('dialog', dialog => dialog.accept());

        const deleteBtn = page.locator('tr', { hasText: 'test-knowledge.txt' })
            .getByRole('button')
            .filter({ has: page.locator('svg.lucide-trash') }); // Specific trash icon

        await deleteBtn.click();

        // Verify deleted
        await expect(page.getByRole('cell', { name: 'test-knowledge.txt' })).not.toBeVisible({ timeout: 10000 });
    });
});
