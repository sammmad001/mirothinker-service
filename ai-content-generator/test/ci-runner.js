/**
 * ContentAI CI 测试运行器
 * 用于持续集成环境
 */

const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = 'file://' + path.resolve(__dirname, '../dist/index.html');

async function runCI() {
  console.log('🚀 ContentAI CI Test Runner');
  console.log('='.repeat(50));

  let browser;
  let passed = 0;
  let failed = 0;

  try {
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    // 设置超时
    page.setDefaultTimeout(10000);

    console.log('\n📋 Running CI tests...\n');

    // 测试1: 页面加载
    try {
      await page.goto(BASE_URL);
      const title = await page.title();
      if (title.includes('ContentAI')) {
        console.log('✅ Test 1: Page load - PASSED');
        passed++;
      } else {
        console.log('❌ Test 1: Page load - FAILED (wrong title)');
        failed++;
      }
    } catch (e) {
      console.log('❌ Test 1: Page load - FAILED');
      failed++;
    }

    // 测试2: 关键元素存在
    try {
      const elements = ['h1', '#product', '#generateBtn', '.pricing'];
      for (const selector of elements) {
        await page.waitForSelector(selector, { timeout: 5000 });
      }
      console.log('✅ Test 2: Critical elements - PASSED');
      passed++;
    } catch (e) {
      console.log('❌ Test 2: Critical elements - FAILED');
      failed++;
    }

    // 测试3: 表单功能
    try {
      await page.fill('#product', 'Test Coffee');
      await page.fill('#brand', 'TestBrand');
      await page.click('#generateBtn');
      await page.waitForTimeout(3000);
      console.log('✅ Test 3: Form functionality - PASSED');
      passed++;
    } catch (e) {
      console.log('❌ Test 3: Form functionality - FAILED');
      failed++;
    }

    // 测试4: 结果生成
    try {
      const resultsVisible = await page.$eval('#results', el => el.style.display !== 'none');
      if (resultsVisible) {
        console.log('✅ Test 4: Content generation - PASSED');
        passed++;
      } else {
        console.log('❌ Test 4: Content generation - FAILED');
        failed++;
      }
    } catch (e) {
      console.log('❌ Test 4: Content generation - FAILED');
      failed++;
    }

    // 测试5: 定价卡片
    try {
      const priceCards = await page.$$('.price-card');
      if (priceCards.length >= 3) {
        console.log('✅ Test 5: Pricing section - PASSED');
        passed++;
      } else {
        console.log('❌ Test 5: Pricing section - FAILED');
        failed++;
      }
    } catch (e) {
      console.log('❌ Test 5: Pricing section - FAILED');
      failed++;
    }

    // 总结
    console.log('\n' + '='.repeat(50));
    console.log(`📊 CI Results: ${passed} passed, ${failed} failed`);
    console.log('='.repeat(50));

    await browser.close();

    return failed === 0;

  } catch (error) {
    console.error('❌ CI runner error:', error.message);
    if (browser) await browser.close();
    return false;
  }
}

// 运行测试
runCI()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
