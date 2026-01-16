const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const providers = [
    { name: 'wiser-human-ai', id: '2004462284' },
    { name: 'PaPa-1', id: '2004724179' },
    { name: 'PaPa-2', id: '2004708868' },
    { name: 'bot-jiap', id: '1656326817' }
  ];

  let allChannels = [];

  for (const provider of providers) {
    console.log('\n=== Checking provider: ' + provider.name + ' (' + provider.id + ') ===');
    await page.goto('https://developers.line.biz/console/provider/' + provider.id);
    await page.waitForTimeout(3000);

    // Take screenshot of provider page
    await page.screenshot({ path: 'provider_' + provider.id + '.png', fullPage: true });

    // Get all links on page
    const links = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('a')).map(a => ({
        text: a.innerText.trim(),
        href: a.href
      }));
    });

    // Filter for channel links
    const channelLinks = links.filter(l => l.href && l.href.includes('/channel/') && !l.href.includes('/settings'));
    console.log('Channel links found:', JSON.stringify(channelLinks, null, 2));

    for (const ch of channelLinks) {
      const match = ch.href.match(/\/channel\/(\d+)/);
      if (match) {
        allChannels.push({
          provider: provider.name,
          providerId: provider.id,
          channelId: match[1],
          channelName: ch.text,
          href: ch.href
        });
      }
    }
  }

  console.log('\n=== All Channels Found ===');
  console.log(JSON.stringify(allChannels, null, 2));
  fs.writeFileSync('all_channels.json', JSON.stringify(allChannels, null, 2));

  // Now get credentials for the first channel with Messaging API
  if (allChannels.length > 0) {
    const channel = allChannels[0];
    console.log('\n=== Getting credentials for: ' + channel.channelName + ' ===');

    // Go to basics page
    await page.goto('https://developers.line.biz/console/channel/' + channel.channelId + '/basics');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'channel_basics.png', fullPage: true });

    // Get page text
    const basicsText = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync('channel_basics.txt', basicsText);

    // Go to messaging API page
    await page.goto('https://developers.line.biz/console/channel/' + channel.channelId + '/messaging-api');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'channel_messaging.png', fullPage: true });

    const messagingText = await page.evaluate(() => document.body.innerText);
    fs.writeFileSync('channel_messaging.txt', messagingText);
  }

  console.log('\nDone! Check the saved files. Browser closing in 30 seconds...');
  await page.waitForTimeout(30000);
  await browser.close();
})();
