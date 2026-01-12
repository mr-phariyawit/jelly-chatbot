const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('Opening LINE Developers Console...');
  await page.goto('https://developers.line.biz/console/');
  
  // Wait for user to log in if needed
  console.log('Waiting for console to load (log in if prompted)...');
  
  // Wait for the provider list or channel list to appear
  await page.waitForSelector('[class*="provider"], [class*="channel"], .console-home', { timeout: 120000 });
  
  console.log('Console loaded. Looking for channels...');
  
  // Take screenshot
  await page.screenshot({ path: 'line_console.png' });
  console.log('Screenshot saved to line_console.png');
  
  // Try to find and list all providers/channels
  const providers = await page.$$eval('a[href*="/provider/"]', links => 
    links.map(l => ({ text: l.textContent?.trim(), href: l.href }))
  );
  
  console.log('Providers found:', JSON.stringify(providers, null, 2));
  
  // Keep browser open for manual inspection
  console.log('\nBrowser is open. Press Ctrl+C when done.');
  await page.waitForTimeout(300000); // Wait 5 minutes
  
  await browser.close();
})();
