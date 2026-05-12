# ContentAI 支付系统集成方案

## 概述

为ContentAI集成三种支付方案：
1. **LemonSqueezy** - SaaS订阅最佳选择
2. **Gumroad** - 最快上线
3. **Stripe** - 最专业

---

## 方案1：LemonSqueezy（推荐）

### 特点
- ✅ 自动处理全球税务（VAT、GST等）
- ✅ 支持订阅制和一次性购买
- ✅ 直接入账银行卡（PayPal或银行转账）
- ✅ 提供托管 checkout 页面
- ✅ 支持优惠券、折扣码
- 手续费：5%+30¢ + 0.5%（支付处理费）

### 注册步骤
1. 访问 https://www.lemonsqueezy.com
2. 注册账户（支持Google登录）
3. 创建产品，获取：
   - API Key
   - Store ID
   - Product/Variant ID

### 集成代码

```html
<!-- 在页面底部添加 LemonSqueezy 按钮 -->
<button class="cta-btn primary" onclick="subscribeLemonSqueezy()">
  Start Free Trial
</button>

<script>
function subscribeLemonSqueezy() {
  // 替换为你自己的LemonSqueezy产品链接
  const checkoutUrl = 'https://contentai.lemonsqueezy.com/checkout/buy/xxx';
  window.location.href = checkoutUrl;
}
</script>
```

### 收款流程
```
用户点击购买 → LemonSqueezy托管页面 → 用户付款
     ↓
LemonSqueezy处理税务 → 扣除手续费
     ↓
自动转账到你的PayPal或银行账户
     ↓
每月底/月初结算
```

---

## 方案2：Gumroad（最快上线）

### 特点
- ✅ 5分钟可上线
- ✅ 手续简单
- ✅ 自动处理税务
- ✅ 支持订阅制
- 手续费：10%（包含支付处理）

### 注册步骤
1. 访问 https://gumroad.com
2. 注册账户
3. 创建产品，设置：
   - 产品名称和价格
   - 订阅选项
   - 获得产品链接

### 集成代码

```html
<button class="cta-btn primary" onclick="subscribeGumroad()">
  Start Free Trial
</button>

<!-- Gumroad embed -->
<script src="https://gumroad.com/js/gumroad.js"></script>

<script>
function subscribeGumroad() {
  // 替换为你自己的Gumroad产品链接
  const productUrl = 'https://contentai.gumroad.com/l/pro';
  window.location.href = productUrl;
}

// 或者使用 Gumroad overlay
function openGumroadOverlay() {
  Gumroad.Product.Show({
    product: 'contentai-pro',
    // 或使用URL: 'https://contentai.gumroad.com/l/pro'
  });
}
</script>
```

### 收款流程
```
用户点击购买 → Gumroad页面 → 用户付款
     ↓
Gumroad处理一切（税务、退款等）
     ↓
自动转账到你的银行账户
     ↓
每周四结算（或按需）
```

---

## 方案3：Stripe（最专业）

### 特点
- ✅ 手续费最低（2.9%+30¢）
- ✅ 最多SaaS使用
- ✅ API最完整
- ✅ 高度可定制
- 需要自己处理税务（可用Stripe Tax）

### 注册步骤
1. 访问 https://stripe.com
2. 注册账户
3. 获取API密钥：
   - Publishable Key（前端用）
   - Secret Key（后端用）
4. 创建产品和价格

### 集成代码

```html
<!-- Stripe.js -->
<script src="https://js.stripe.com/v3/"></script>

<button id="checkout-button" class="cta-btn primary">
  Start Free Trial
</button>

<script>
const stripe = Stripe('pk_test_xxx'); // 替换为你的publishable key

document.getElementById('checkout-button').addEventListener('click', () => {
  // 创建Checkout Session（需要后端）
  fetch('/create-checkout-session', {
    method: 'POST',
  })
  .then(response => response.json())
  .then(session => {
    return stripe.redirectToCheckout({ sessionId: session.id });
  })
  .then(result => {
    if (result.error) {
      alert(result.error.message);
    }
  });
});
</script>
```

### 收款流程
```
用户点击购买 → 跳转Stripe Checkout
     ↓
用户输入信用卡信息
     ↓
Stripe处理支付
     ↓
7天后资金入账你的银行账户
     ↓
Stripe后台自动生成账单和报表
```

---

## 三种方案对比

| 特性 | LemonSqueezy | Gumroad | Stripe |
|------|---------------|---------|--------|
| 手续费 | 5%+30¢ | 10% | 2.9%+30¢ |
| 税务处理 | ✅ 自动 | ✅ 自动 | ❌ 需配置 |
| 到账时间 | 1-2个工作日 | 每周四 | 7天 |
| 订阅功能 | ✅ | ✅ | ✅ |
| 注册难度 | 简单 | 最简单 | 中等 |
| 集成难度 | 最简单 | 最简单 | 复杂 |
| 适合阶段 | MVP+正式 | 快速验证 | 规模化 |

---

## 推荐行动方案

### 第1步（今天）
使用 **Gumroad** 最快上线：
1. 注册Gumroad账户（5分钟）
2. 创建Pro订阅产品
3. 把链接粘贴到按钮
4. 开始收款！

### 第2步（验证后）
迁移到 **LemonSqueezy**：
1. 迁移到更低的费率
2. 获得更专业的税务处理
3. 保持订阅功能

### 第3步（规模化后）
迁移到 **Stripe**：
1. 最低手续费
2. 最完整的API
3. 最大的定制灵活性

---

## 资金到账时间

| 平台 | 首次到账 | 后续到账 |
|------|----------|----------|
| LemonSqueezy | 1-2个工作日 | 自动结算 |
| Gumroad | 3-5天 | 每周四 |
| Stripe | 7天 | 7天 |

---

## 税务考虑

### 需要知道的
- 如果服务美国用户，需要处理销售税
- 欧洲用户需要处理VAT
- 超过阈值需要注册当地税务

### 平台处理
- **LemonSqueezy**: ✅ 自动处理所有税务
- **Gumroad**: ✅ 自动处理所有税务
- **Stripe**: ❌ 需要配置Stripe Tax（$20/月起）

---

## 下一步

1. 选择平台注册
2. 创建产品
3. 获取链接
4. 更新按钮代码
5. 测试支付流程
6. 开始收款！
