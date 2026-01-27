import { test, expect } from '@playwright/test';

test('Create Bot from bot-test.txt credentials and verify Analysis', async ({ page }) => {
  // 1. Navigate to Bots Page (Bypass auth if possible, or assume public for now as per config)
  await page.goto('/admin/bots');

  // Handle potential login verify (if redirected)
  // For this environment, we assume we might need to be in 'admin' mode
  // The middleware.ts suggests /admin is protected. 
  // Ideally we should mock auth, but for "via playwright" as a tool, we might need to handle it.
  // Given previous tests used direct API or assumed env, let's try UI interaction.
  
  // If we see a login screen, we might fail. 
  // However, I'll assume the previous `ai-analysis.spec.ts` struggle implies we need a robust approach.
  // Wait, `ai-analysis.spec.ts` was refactored to use API directly because of Auth issues.
  // The user asked "Create bot detail ... via playwright". They probably want the UI actions to be performed.
  // I will try to perform UI actions. If auth blocks, I'll use the API to "Login" or set a cookie.
  
  // 2. Click Create Bot
  await page.click('button:has-text("Create Bot")');

  // 3. Fill Form
  await page.fill('input[name="name"]', 'LINE Integration Test Bot');
  await page.fill('textarea[name="description"]', 'Bot created via Playwright using bot-test.txt credentials. Basic ID: @073upziw');
  
  await page.fill('input[name="channel_id"]', '2008690282');
  await page.fill('input[name="channel_secret"]', 'd0bcaa5333ac29f1b65b0a204268fe8a');
  await page.fill('input[name="user_id"]', 'U4bc18b6ecbdc3f7984b2e249d16c854f');
  
  const token = '0CTKYq9cLZJJIQJRufb1ozz52/njox/wjMHbT8JDMdzi6Xe2GtkUSmGRCxQKfHxS4aUs2xodx+eNWTanqhcMV3Ptd2TuNCahyUnEREagEU6C4Ti/BEDqVnca/sLiDvNdoSrlmgH5Hsq5t/l+dIXDWwdB04t89/1O/w1cDnyilFU=';
  await page.fill('textarea[name="channel_access_token"]', token);

  // 4. Submit
  await page.click('button:has-text("Create New Bot")'); // Text inside Dialog Footer

  // 5. Verify Bot Created (Wait for toast or list update)
  await expect(page.getByText('Bot created successfully')).toBeVisible();
  
  // 6. Navigate to Bot Details
  // Click on the Card Title "LINE Integration Test Bot"
  await page.click('h3:has-text("LINE Integration Test Bot")');

  // 7. Upload File
  // Prepare file path
  const filePath = '/Users/mr.phariyawit/Documents/ai-support/bot-test.txt';
  
  // Trigger file upload
  // Looking for <Input type="file">. It's usually hidden.
  // In `page.tsx`: <Input type="file" ... onChange={handleUpload} ... />
  // We need to set input files.
  const fileInput = await page.locator('input[type="file"]');
  await fileInput.setInputFiles(filePath);
  
  // Wait for upload success
  await expect(page.getByText('File uploaded successfully')).toBeVisible();
  
  // 8. Trigger Analysis
  // Find the row with "bot-test.txt"
  const row = page.locator('tr').filter({ hasText: 'bot-test.txt' });
  
  // Click the "Wand" button (Auto-Analyze)
  // Tooltip is "Auto-Analyze Context"
  await row.getByRole('button', { name: 'Auto-Analyze Context' }).click();

  // 9. Verify Auto-Save & Modal
  // Expect Toast "AI Analysis complete"
  await expect(page.getByText('AI Analysis complete')).toBeVisible({ timeout: 30000 });
  
  // Expect Modal to open
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByText('File Context Analysis')).toBeVisible();
  
  // 10. Save from Modal
  await page.click('button:has-text("Save Changes")');
  await expect(page.getByText('File description updated')).toBeVisible();
});
