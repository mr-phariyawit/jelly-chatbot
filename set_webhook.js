const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const webhookUrl = 'https://session-api-182206907696.us-central1.run.app/webhook/3d28a8d5';
  const channelId = '2008690282';

  try {
    console.log('Opening LINE Developers Console...');
    await page.goto('https://developers.line.biz/console/channel/' + channelId + '/messaging-api', { timeout: 30000 });

    // Wait for login if needed
    await page.waitForSelector('input, button, [class*="webhook"]', { timeout: 120000 });
    console.log('Page loaded');

    await page.waitForTimeout(3000);

    // Look for webhook URL input
    const webhookInput = await page.$('input[placeholder*="webhook"], input[name*="webhook"], input[type="url"]');
    if (webhookInput) {
      console.log('Found webhook input, setting URL...');
      await webhookInput.fill('');
      await webhookInput.fill(webhookUrl);
      console.log('Webhook URL set');
    }

    // Look for Edit button first
    const editBtn = await page.$('button:has-text("Edit")');
    if (editBtn) {
      console.log('Clicking Edit button...');
      await editBtn.click();
      await page.waitForTimeout(2000);

      // Now find the input again
      const input = await page.$('input[type="url"], input[placeholder*="http"]');
      if (input) {
        await input.fill(webhookUrl);
        console.log('URL filled');

        // Click Update or Save
        const updateBtn = await page.$('button:has-text("Update"), button:has-text("Save")');
        if (updateBtn) {
          await updateBtn.click();
          console.log('Clicked Update');
          await page.waitForTimeout(2000);
        }
      }
    }

    // Enable webhook toggle
    const toggles = await page.$$('input[type="checkbox"], [role="switch"]');
    for (const toggle of toggles) {
      const parent = await toggle.evaluateHandle(el => el.closest('label, div'));
      const text = await parent.evaluate(el => el.innerText || '');
      if (text.toLowerCase().includes('use webhook')) {
        const isChecked = await toggle.isChecked();
        if (!isChecked) {
          console.log('Enabling Use webhook toggle...');
          await toggle.click();
          await page.waitForTimeout(1000);
        } else {
          console.log('Webhook already enabled');
        }
      }
    }

    await page.screenshot({ path: 'webhook_set.png', fullPage: true });
    console.log('\nScreenshot saved. Please verify the webhook is set correctly.');
    console.log('Webhook URL:', webhookUrl);

  } catch (err) {
    console.error('Error:', err.message);
  }

  console.log('\nBrowser closing in 30 seconds...');
  await page.waitForTimeout(30000);
  await browser.close();
})();
