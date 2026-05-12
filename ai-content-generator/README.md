# ContentAI - AI Social Media Content Generator

## 快速启动

### 方式1：直接打开
直接在浏览器中打开 `index.html` 文件即可预览产品。

### 方式2：本地服务器
```bash
# 使用 Python
python -m http.server 8000

# 或使用 Node.js
npx serve
```

然后访问 http://localhost:8000

---

## 项目结构

```
ai-content-generator/
├── index.html          # 完整的可运行HTML应用
├── app/
│   ├── layout.js       # Next.js 布局
│   ├── page.js        # Next.js 主页面
│   └── globals.css    # Tailwind 样式
├── package.json        # 依赖配置
├── next.config.js     # Next.js 配置
├── tailwind.config.js # Tailwind 配置
└── README.md          # 本文件
```

---

## 部署到 Vercel

1. 在 GitHub 创建仓库并推送代码
2. 访问 vercel.com
3. Import 项目
4. Deploy

---

## 部署到 Netlify

1. 将 `index.html` 拖拽到 Netlify Drop
2. 即时部署完成

---

## 商业模式

### 收入来源
1. **订阅制 SaaS**
   - Free: 5次/天生成
   - Pro: $9.99/月 无限制
   - Enterprise: $29/月 团队版

2. **定制开发服务**
   - AI工具定制开发
   - 品牌内容生成器定制

3. **联盟推广**
   - 推广AI工具获取佣金

---

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (原生)
- **AI集成**: OpenAI API (生产环境)
- **部署**: Vercel / Netlify / Cloudflare Pages

---

## 下一步

1. [ ] 申请 OpenAI API Key
2. [ ] 集成真实 AI 生成功能
3. [ ] 添加用户认证系统
4. [ ] 集成 Stripe/Paddle 支付
5. [ ] 配置自定义域名
6. [ ] 发布到 Product Hunt
7. [ ] 开始获取第一批付费用户
