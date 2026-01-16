const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Load existing credentials
  const creds = JSON.parse(fs.readFileSync('line_credentials.json', 'utf8'));

  try {
    console.log('Opening LINE Developers Console...');
    await page.goto('https://developers.line.biz/console/', { timeout: 30000 });

    // Wait for login
    await page.waitForSelector('a[href*="/provider/"]', { timeout: 120000 });
    console.log('Logged in!\n');

    for (let i = 0; i < creds.length; i++) {
      const cred = creds[i];
      console.log('--- Processing:', cred.channelName.replace(/\n/g, ' '), '---');

      // Go to Messaging API page
      await page.goto('https://developers.line.biz/console/channel/' + cred.channelId + '/messaging-api', { timeout: 30000 });
      await page.waitForTimeout(3000);

      // Look for existing token
      let token = null;
      const textareas = await page.$$('textarea');
      for (const ta of textareas) {
        const val = await ta.inputValue();
        if (val && val.length > 100) {
          token = val;
          break;
        }
      }

      if (!token) {
        // Try to find Issue button
        console.log('  Looking for Issue button...');
        const buttons = await page.$$('button');
        for (const btn of buttons) {
          const text = await btn.innerText();
          if (text.includes('Issue')) {
            console.log('  Clicking Issue...');
            await btn.click();
            await page.waitForTimeout(5000);

            // Check for textarea again
            const newTextareas = await page.$$('textarea');
            for (const ta of newTextareas) {
              const val = await ta.inputValue();
              if (val && val.length > 100) {
                token = val;
                break;
              }
            }
            break;
          }
        }
      }

      if (token) {
        creds[i].accessToken = token;
        console.log('  Token:', token.substring(0, 40) + '...');
      } else {
        console.log('  No token found');
      }

      await page.waitForTimeout(1000);
    }

    console.log('\n\n========== UPDATED CREDENTIALS ==========');
    console.log(JSON.stringify(creds, null, 2));
    fs.writeFileSync('line_credentials.json', JSON.stringify(creds, null, 2));
    console.log('\nSaved to line_credentials.json');

  } catch (err) {
    console.error('Error:', err.message);
  }

  console.log('\nBrowser closing in 5 seconds...');
  await page.waitForTimeout(5000);
  await browser.close();
})();
