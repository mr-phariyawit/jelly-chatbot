const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Opening LINE Developers Console...');
    console.log('Please log in if prompted. Waiting up to 2 minutes...\n');

    await page.goto('https://developers.line.biz/console/', { timeout: 30000 });

    // Wait for login to complete - look for provider or channel elements
    await page.waitForSelector('a[href*="/provider/"], a[href*="/channel/"], [class*="provider"], [class*="channel"]', {
      timeout: 120000
    });

    console.log('Logged in! Scanning for channels...\n');
    await page.waitForTimeout(2000);

    // Get all provider links
    const providerLinks = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a[href*="/provider/"]'));
      return links.map(l => ({
        text: l.innerText.trim().substring(0, 50),
        href: l.href,
        providerId: l.href.match(/\/provider\/(\d+)/)?.[1]
      })).filter(l => l.providerId);
    });

    console.log('Providers found:', providerLinks.length);

    // Dedupe providers
    const uniqueProviders = [...new Map(providerLinks.map(p => [p.providerId, p])).values()];
    console.log('Unique providers:', JSON.stringify(uniqueProviders, null, 2));

    let allCredentials = [];

    for (const provider of uniqueProviders) {
      console.log('\n--- Checking provider:', provider.text, '---');
      await page.goto('https://developers.line.biz/console/provider/' + provider.providerId, { timeout: 30000 });
      await page.waitForTimeout(2000);

      // Find Messaging API channels
      const channels = await page.evaluate(() => {
        const items = Array.from(document.querySelectorAll('a[href*="/channel/"]'));
        return items.map(el => ({
          text: el.innerText.trim().substring(0, 100),
          href: el.href,
          channelId: el.href.match(/\/channel\/(\d+)/)?.[1]
        })).filter(c => c.channelId && !c.href.includes('/settings'));
      });

      // Dedupe channels
      const uniqueChannels = [...new Map(channels.map(c => [c.channelId, c])).values()];
      console.log('Channels:', uniqueChannels.map(c => c.text + ' (' + c.channelId + ')'));

      for (const channel of uniqueChannels) {
        console.log('\n  Getting credentials for:', channel.text);

        let creds = {
          provider: provider.text,
          providerId: provider.providerId,
          channelName: channel.text,
          channelId: channel.channelId,
          channelSecret: null,
          accessToken: null
        };

        // Get basics page for Channel ID and Secret
        await page.goto('https://developers.line.biz/console/channel/' + channel.channelId + '/basics', { timeout: 30000 });
        await page.waitForTimeout(2000);

        const basicsText = await page.evaluate(() => document.body.innerText);

        // Extract Channel Secret (32 hex chars after "Channel secret")
        const secretMatch = basicsText.match(/Channel secret\s*\n?\s*([a-f0-9]{32})/i);
        if (secretMatch) {
          creds.channelSecret = secretMatch[1];
          console.log('  Channel Secret:', creds.channelSecret.substring(0, 10) + '...');
        }

        // Go to Messaging API page
        await page.goto('https://developers.line.biz/console/channel/' + channel.channelId + '/messaging-api', { timeout: 30000 });
        await page.waitForTimeout(2000);

        // Try to find access token
        const tokenTextarea = await page.$('textarea');
        if (tokenTextarea) {
          const token = await tokenTextarea.inputValue();
          if (token && token.length > 50) {
            creds.accessToken = token;
            console.log('  Access Token:', token.substring(0, 30) + '...');
          }
        }

        // If no token, try to issue one
        if (!creds.accessToken) {
          const issueBtn = await page.$('button:has-text("Issue")');
          if (issueBtn) {
            console.log('  Clicking Issue button...');
            await issueBtn.click();
            await page.waitForTimeout(3000);

            const newTextarea = await page.$('textarea');
            if (newTextarea) {
              const token = await newTextarea.inputValue();
              if (token && token.length > 50) {
                creds.accessToken = token;
                console.log('  New Access Token:', token.substring(0, 30) + '...');
              }
            }
          }
        }

        allCredentials.push(creds);
      }
    }

    console.log('\n\n========== ALL CREDENTIALS ==========');
    console.log(JSON.stringify(allCredentials, null, 2));
    fs.writeFileSync('line_credentials.json', JSON.stringify(allCredentials, null, 2));
    console.log('\nSaved to line_credentials.json');

  } catch (err) {
    console.error('Error:', err.message);
  }

  console.log('\nBrowser closing in 10 seconds...');
  await page.waitForTimeout(10000);
  await browser.close();
})();
