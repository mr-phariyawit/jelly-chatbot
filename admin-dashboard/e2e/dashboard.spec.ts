import { test, expect } from '@playwright/test';

const TARGET_URL = 'https://admin-dashboard-687023036300.us-central1.run.app';

test.describe('Admin Dashboard', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(TARGET_URL);
    });

    test('should load the dashboard and redirect to bots page', async ({ page }) => {
        // Assert we are redirected to /admin/bots
        await expect(page).toHaveURL(/.*\/admin\/bots/);

        // Check for main heading
        await expect(page.getByRole('heading', { name: 'Bots' })).toBeVisible();
    });

    test('should open create bot dialog', async ({ page }) => {
        // Click Create Bot button
        await page.getByRole('button', { name: 'Create Bot' }).click();

        // Dialog should appear
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Create New Bot' })).toBeVisible();
    });

    test('should navigate to sessions', async ({ page }) => {
        // Click Sessions link in sidebar
        await page.getByRole('link', { name: 'Sessions' }).click();

        // URL should change
        await expect(page).toHaveURL(/.*\/admin\/sessions/);

        // Wait for potential loading state
        await expect(page.getByText('Loading sessions...').or(page.getByRole('heading', { name: 'Sessions' }))).toBeVisible({ timeout: 10000 });

        // Improve reliability: if loading is visible, wait for it to detach
        if (await page.getByText('Loading sessions...').isVisible()) {
            await expect(page.getByText('Loading sessions...')).not.toBeVisible({ timeout: 30000 });
        }

        // Heading should be visible eventually
        await expect(page.getByRole('heading', { name: 'Sessions' })).toBeVisible();
    });
});
