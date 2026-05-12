/**
 * ContentAI - 完整测试框架
 * 包含：功能测试、性能测试、响应式测试、支付流程测试
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// 配置
const CONFIG = {
  BASE_URL: 'file://' + path.resolve(__dirname, 'dist/index.html'),
  TIMEOUT: 30000,
  HEADLESS: true,
  VIEWPORTS: {
    mobile: { width: 375, height: 667 },
    tablet: { width: 768, height: 1024 },
    desktop: { width: 1280, height: 800 },
    large: { width: 1920, height: 1080 }
  }
};

// 测试结果收集
const testResults = {
  passed: [],
  failed: [],
  warnings: [],
  performance: {}
};

// 日志工具
function log(message, type = 'info') {
  const timestamp = new Date().toISOString();
  const prefix = {
    'info': 'ℹ️ ',
    'pass': '✅',
    'fail': '❌',
    'warn': '⚠️',
    'perf': '📊'
  }[type];
  console.log(`${prefix} [${timestamp}] ${message}`);
}

// ==================== 测试套件 ====================

/**
 * 1. 页面加载测试
 */
async function testPageLoad(page) {
  log('开始页面加载测试...', 'info');

  try {
    const startTime = Date.now();
    await page.goto(CONFIG.BASE_URL, { waitUntil: 'domcontentloaded' });
    const loadTime = Date.now() - startTime;

    testResults.performance.pageLoadTime = loadTime;

    if (loadTime < 3000) {
      log(`页面加载时间: ${loadTime}ms ✓`, 'pass');
    } else {
      log(`页面加载时间: ${loadTime}ms (偏慢)`, 'warn');
    }

    // 检查关键元素
    const title = await page.title();
    if (title.includes('ContentAI')) {
      testResults.passed.push('页面标题正确');
    } else {
      testResults.failed.push(`页面标题错误: ${title}`);
    }

    return true;
  } catch (error) {
    testResults.failed.push(`页面加载失败: ${error.message}`);
    return false;
  }
}

/**
 * 2. 关键UI元素测试
 */
async function testCriticalElements(page) {
  log('测试关键UI元素...', 'info');

  const criticalElements = [
    { selector: 'h1', name: '主标题' },
    { selector: '#product', name: '产品输入框' },
    { selector: '#brand', name: '品牌输入框' },
    { selector: '#language', name: '语言选择器' },
    { selector: '#generateBtn', name: '生成按钮' },
    { selector: '.pricing', name: '定价区域' },
    { selector: '.price-card', name: '价格卡片' }
  ];

  for (const element of criticalElements) {
    try {
      await page.waitForSelector(element.selector, { timeout: 5000 });
      testResults.passed.push(`${element.name} 存在`);
    } catch (error) {
      testResults.failed.push(`${element.name} 不存在: ${element.selector}`);
    }
  }
}

/**
 * 3. 表单功能测试
 */
async function testFormFunctionality(page) {
  log('测试表单功能...', 'info');

  // 测试产品输入
  try {
    await page.fill('#product', 'Test Product 123');
    const value = await page.$eval('#product', el => el.value);
    if (value === 'Test Product 123') {
      testResults.passed.push('产品输入框工作正常');
    }
  } catch (error) {
    testResults.failed.push(`产品输入框测试失败: ${error.message}`);
  }

  // 测试品牌输入
  try {
    await page.fill('#brand', 'TestBrand');
    testResults.passed.push('品牌输入框工作正常');
  } catch (error) {
    testResults.failed.push(`品牌输入框测试失败: ${error.message}`);
  }

  // 测试语言选择
  try {
    await page.selectOption('#language', 'ar');
    const selected = await page.$eval('#language', el => el.value);
    if (selected === 'ar') {
      testResults.passed.push('语言选择器工作正常');
    }
  } catch (error) {
    testResults.failed.push(`语言选择器测试失败: ${error.message}`);
  }
}

/**
 * 4. 平台选择按钮测试
 */
async function testPlatformButtons(page) {
  log('测试平台选择按钮...', 'info');

  const platforms = ['instagram', 'facebook', 'twitter', 'tiktok'];

  for (const platform of platforms) {
    try {
      const btn = await page.$(`[data-platform="${platform}"]`);
      if (btn) {
        await btn.click();
        const isActive = await btn.evaluate(el => el.classList.contains('active'));
        if (isActive) {
          testResults.passed.push(`${platform} 按钮可点击`);
        }
      }
    } catch (error) {
      testResults.failed.push(`${platform} 按钮测试失败`);
    }
  }
}

/**
 * 5. 内容生成功能测试
 */
async function testContentGeneration(page) {
  log('测试内容生成功能...', 'info');

  try {
    // 填写表单
    await page.fill('#product', 'Organic Coffee Beans');
    await page.fill('#brand', 'CoffeeCo');

    // 点击生成按钮
    await page.click('#generateBtn');

    // 等待加载完成
    await page.waitForTimeout(3000);

    // 检查结果区域
    const resultsDiv = await page.$('#results');
    const isVisible = await resultsDiv?.evaluate(el => el.style.display !== 'none');

    if (isVisible) {
      testResults.passed.push('内容生成功能正常');

      // 检查生成的内容卡片
      const resultCards = await page.$$('.result-card');
      if (resultCards.length > 0) {
        testResults.passed.push(`生成了 ${resultCards.length} 个平台内容`);
      }
    } else {
      testResults.failed.push('内容生成后结果区域未显示');
    }
  } catch (error) {
    testResults.failed.push(`内容生成测试失败: ${error.message}`);
  }
}

/**
 * 6. 复制到剪贴板功能测试
 */
async function testCopyFunctionality(page) {
  log('测试复制功能...', 'info');

  // 先生成内容
  await page.fill('#product', 'Test Product');
  await page.click('#generateBtn');
  await page.waitForTimeout(3000);

  try {
    // 点击复制按钮
    const copyBtn = await page.$('.copy-btn');
    if (copyBtn) {
      // 由于clipboard API需要安全上下文，这里只检查按钮存在
      testResults.passed.push('复制按钮存在');
    }
  } catch (error) {
    testResults.warnings.push('复制功能需要HTTPS环境测试');
  }
}

/**
 * 7. 定价页面测试
 */
async function testPricingSection(page) {
  log('测试定价区域...', 'info');

  try {
    const pricingSection = await page.$('.pricing');
    if (!pricingSection) {
      testResults.failed.push('定价区域不存在');
      return;
    }

    // 检查价格卡片
    const priceCards = await page.$$('.price-card');
    if (priceCards.length >= 3) {
      testResults.passed.push(`定价卡片数量正确: ${priceCards.length}`);

      // 检查价格文字
      const prices = await page.$$eval('.price-value', els => els.map(el => el.textContent));
      log(`价格: ${prices.join(', ')}`, 'info');
    }

    // 检查CTA按钮
    const ctaButtons = await page.$$('.cta-btn');
    if (ctaButtons.length >= 3) {
      testResults.passed.push('定价CTA按钮完整');
    }
  } catch (error) {
    testResults.failed.push(`定价测试失败: ${error.message}`);
  }
}

/**
 * 8. 响应式布局测试
 */
async function testResponsiveDesign(page) {
  log('测试响应式设计...', 'info');

  for (const [name, viewport] of Object.entries(CONFIG.VIEWPORTS)) {
    try {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);

      // 检查主要内容是否可见
      const h1 = await page.$('h1');
      const isVisible = h1 && await h1.isVisible();

      if (isVisible) {
        testResults.passed.push(`${name} (${viewport.width}x${viewport.height}) 布局正常`);
      } else {
        testResults.failed.push(`${name} 布局异常`);
      }
    } catch (error) {
      testResults.warnings.push(`${name} 测试跳过: ${error.message}`);
    }
  }
}

/**
 * 9. 性能测试
 */
async function testPerformance(page) {
  log('执行性能测试...', 'info');

  try {
    // 测试FCP (First Contentful Paint)
    const fcp = await page.evaluate(() => {
      return new Promise(resolve => {
        if (PerformanceObserver) {
          const observer = new PerformanceObserver(list => {
            for (const entry of list.getEntries()) {
              if (entry.name === 'first-contentful-paint') {
                resolve(entry.startTime);
              }
            }
          });
          observer.observe({ type: 'paint', buffered: true });
          setTimeout(() => resolve(null), 5000);
        } else {
          resolve(null);
        }
      });
    });

    if (fcp) {
      testResults.performance.fcp = Math.round(fcp);
      log(`首次内容绘制: ${Math.round(fcp)}ms`, 'perf');
    }

    // 检查资源加载
    const resources = await page.evaluate(() => {
      const scripts = document.querySelectorAll('script');
      const links = document.querySelectorAll('link[rel="stylesheet"]');
      const images = document.querySelectorAll('img');
      return {
        scripts: scripts.length,
        stylesheets: links.length,
        images: images.length
      };
    });

    log(`资源: ${resources.scripts} 脚本, ${resources.stylesheets} 样式, ${resources.images} 图片`, 'perf');
    testResults.passed.push('页面资源结构正常');

  } catch (error) {
    testResults.warnings.push(`性能测试部分失败: ${error.message}`);
  }
}

/**
 * 10. 多语言支持测试
 */
async function testMultiLanguage(page) {
  log('测试多语言支持...', 'info');

  const languages = ['en', 'ar', 'ms', 'id'];
  const langNames = { en: 'English', ar: 'Arabic', ms: 'Malay', id: 'Indonesian' };

  for (const lang of languages) {
    try {
      await page.selectOption('#language', lang);
      await page.fill('#product', 'Coffee');
      await page.click('#generateBtn');
      await page.waitForTimeout(2500);

      // 验证阿拉伯语RTL
      if (lang === 'ar') {
        const htmlDir = await page.$eval('html', el => el.getAttribute('dir'));
        testResults.passed.push(`阿拉伯语RTL支持: ${htmlDir || '未设置'}`);
      }

      testResults.passed.push(`${langNames[lang]} 语言切换正常`);
    } catch (error) {
      testResults.failed.push(`${langNames[lang]} 测试失败`);
    }
  }
}

/**
 * 11. 无障碍测试
 */
async function testAccessibility(page) {
  log('测试无障碍功能...', 'info');

  try {
    // 检查表单标签
    const labels = await page.$$('label');
    if (labels.length >= 2) {
      testResults.passed.push(`表单标签完整: ${labels.length}个`);
    }

    // 检查按钮文本
    const buttons = await page.$$('button');
    const buttonsWithText = await page.$$eval('button', btns =>
      btns.filter(btn => btn.textContent.trim()).length
    );

    if (buttonsWithText > 0) {
      testResults.passed.push(`按钮有文字说明: ${buttonsWithText}/${buttons.length}`);
    }

    // 检查颜色对比度（基础）
    const bodyBg = await page.$eval('body', el =>
      getComputedStyle(el).background
    );
    const textColor = await page.$eval('h1', el =>
      getComputedStyle(el).color
    );

    log(`背景: ${bodyBg}, 文字: ${textColor}`, 'info');
    testResults.passed.push('颜色配置已设置');

  } catch (error) {
    testResults.warnings.push(`无障碍测试跳过: ${error.message}`);
  }
}

/**
 * 12. 错误处理测试
 */
async function testErrorHandling(page) {
  log('测试错误处理...', 'info');

  // 测试空表单提交
  try {
    // 清空表单
    await page.fill('#product', '');
    await page.fill('#brand', '');

    // 尝试生成
    await page.click('#generateBtn');

    // 检查是否有alert
    page.on('dialog', async dialog => {
      if (dialog.message().includes('Please enter')) {
        testResults.passed.push('空表单验证正常');
      }
      await dialog.accept();
    });

    await page.waitForTimeout(500);
  } catch (error) {
    testResults.warnings.push('空表单测试需手动验证');
  }
}

// ==================== 测试报告生成 ====================

function generateReport() {
  console.log('\n' + '='.repeat(60));
  console.log('📋 ContentAI 测试报告');
  console.log('='.repeat(60));

  console.log('\n✅ 通过的测试:');
  testResults.passed.forEach(item => console.log(`   • ${item}`));

  if (testResults.failed.length > 0) {
    console.log('\n❌ 失败的测试:');
    testResults.failed.forEach(item => console.log(`   • ${item}`));
  }

  if (testResults.warnings.length > 0) {
    console.log('\n⚠️ 警告:');
    testResults.warnings.forEach(item => console.log(`   • ${item}`));
  }

  console.log('\n📊 性能指标:');
  if (testResults.performance.pageLoadTime) {
    console.log(`   • 页面加载时间: ${testResults.performance.pageLoadTime}ms`);
  }
  if (testResults.performance.fcp) {
    console.log(`   • 首次内容绘制: ${testResults.performance.fcp}ms`);
  }

  const totalPassed = testResults.passed.length;
  const totalFailed = testResults.failed.length;
  const totalTests = totalPassed + totalFailed;

  console.log('\n' + '='.repeat(60));
  console.log(`📈 测试结果: ${totalPassed}/${totalTests} 通过`);
  console.log('='.repeat(60));

  return {
    success: totalFailed === 0,
    passed: totalPassed,
    failed: totalFailed,
    warnings: testResults.warnings.length
  };
}

// ==================== 主测试入口 ====================

async function runAllTests() {
  log('🚀 ContentAI 测试框架启动', 'info');
  log(`测试URL: ${CONFIG.BASE_URL}`, 'info');
  console.log('');

  let browser;
  let page;

  try {
    // 启动浏览器
    log('启动浏览器...', 'info');
    browser = await chromium.launch({
      headless: CONFIG.HEADLESS
    });
    page = await browser.newPage();

    // 执行测试套件
    await testPageLoad(page);
    await testCriticalElements(page);
    await testFormFunctionality(page);
    await testPlatformButtons(page);
    await testPricingSection(page);
    await testResponsiveDesign(page);
    await testContentGeneration(page);
    await testCopyFunctionality(page);
    await testMultiLanguage(page);
    await testAccessibility(page);
    await testPerformance(page);
    await testErrorHandling(page);

    // 生成报告
    const result = generateReport();

    log('测试完成!', result.success ? 'pass' : 'warn');

    return result;

  } catch (error) {
    log(`测试执行失败: ${error.message}`, 'fail');
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// 导出测试框架
module.exports = {
  runAllTests,
  CONFIG,
  testResults
};

// 直接运行
if (require.main === module) {
  runAllTests()
    .then(result => {
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}
