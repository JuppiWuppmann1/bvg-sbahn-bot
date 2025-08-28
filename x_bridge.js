const puppeteer = require("puppeteer-core");
const fs = require("fs");
const path = require("path");

(async () => {
  const threads = JSON.parse(await new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", chunk => data += chunk);
    process.stdin.on("end", () => resolve(data));
  }));

  const cookies = JSON.parse(fs.readFileSync("x_cookies.json", "utf-8"));

  const browser = await puppeteer.launch({
    headless: true,
    executablePath: "/usr/bin/google-chrome", // oder "/usr/bin/chromium-browser"
    args: ["--no-sandbox"]
  });

  const page = await browser.newPage();
  await page.setCookie(...cookies);
  await page.goto("https://x.com/home", { timeout: 60000 });

  const composeExists = await page.$("a[href='/compose/tweet']");
  if (!composeExists) {
    console.error("❌ Session nicht aktiv – kein Compose-Link gefunden.");
    await page.screenshot({ path: "session_invalid.png" });
    await browser.close();
    process.exit(1);
  }

  for (let i = 0; i < threads.length; i++) {
    const thread = threads[i];
    try {
      console.log(`✍️ Starte Thread ${i + 1}...`);
      await page.goto("https://x.com/compose/tweet", { timeout: 60000 });

      const field = await page.waitForSelector("div[role='textbox']", { timeout: 10000 });
      await field.click();
      await field.type(thread[0]);

      for (let j = 1; j < thread.length; j++) {
        await page.click("div[data-testid='tweetButtonInline']");
        const replyField = await page.waitForSelector("div[role='textbox']", { timeout: 10000 });
        await replyField.click();
        await replyField.type(thread[j]);
      }

      await page.click("div[data-testid='tweetButtonInline']");
      console.log(`✅ Thread ${i + 1} gepostet!`);
    } catch (err) {
      console.error(`❌ Fehler beim Thread ${i + 1}:`, err);
      await page.screenshot({ path: `tweet_error_${i + 1}.png` });
    }
  }

  await browser.close();
})();
