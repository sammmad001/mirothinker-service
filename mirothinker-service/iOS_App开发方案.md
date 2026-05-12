# MiroThinker iOS App 开发方案

> 版本: v1.0 | 2026-05-11

---

## 一、技术方案选择

### 方案对比

| 方案 | 开发成本 | 性能 | 原生体验 | 维护成本 | 推荐度 |
|------|---------|------|---------|---------|--------|
| **Swift 原生** | 高 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | ⭐⭐⭐ |
| **React Native** | 中 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐⭐ |
| **Flutter** | 中 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 低 | ⭐⭐⭐⭐ |
| **WebView 包装** | 低 | ⭐⭐⭐ | ⭐⭐ | 低 | ⭐⭐ |
| **PWA** | 最低 | ⭐⭐⭐ | ⭐⭐ | 最低 | ⭐⭐⭐ |

### 推荐方案

**🎯 React Native** - 最适合你的场景

原因:
1. **后端已存在**: 你已有完整的 REST API，RN 可直接调用
2. **跨平台**: 一套代码同时支持 iOS 和 Android
3. **开发快**: 比原生 Swift 快 40-60%
4. **生态好**: 组件丰富，社区活跃
5. **可复用**: 前端已有的 UI 设计可快速迁移

---

## 二、App 架构设计

```
┌─────────────────────────────────────────────┐
│              MiroThinker iOS App             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │           UI 层 (React Native)       │   │
│  │                                     │   │
│  │  • 首页 (研究表单)                   │   │
│  │  • 任务列表 (历史记录)               │   │
│  │  • 结果展示 (Markdown 渲染)          │   │
│  │  • 设置页面                         │   │
│  └──────────────┬──────────────────────┘   │
│                 │                          │
│  ┌──────────────▼──────────────────────┐   │
│  │         业务逻辑层                   │   │
│  │                                     │   │
│  │  • API 调用封装                      │   │
│  │  • 状态管理 (Redux/Zustand)          │   │
│  │  • 本地缓存 (AsyncStorage)           │   │
│  │  • Markdown 解析                    │   │
│  │  • 推送通知                         │   │
│  └──────────────┬──────────────────────┘   │
│                 │                          │
│  ┌──────────────▼──────────────────────┐   │
│  │         网络层                       │   │
│  │                                     │   │
│  │  • Axios/Fetch                       │   │
│  │  • 请求/响应拦截器                   │   │
│  │  • 离线队列                         │   │
│  └──────────────┬──────────────────────┘   │
│                 │                          │
└─────────────────┼──────────────────────────┘
                  │ REST API
                  ▼
┌─────────────────────────────────────────────┐
│       你的云服务器 (已有)                     │
│       backend/main.py (FastAPI)              │
└─────────────────────────────────────────────┘
```

---

## 三、核心功能清单

### MVP (第一版必需功能)

| 功能 | 优先级 | 说明 |
|------|--------|------|
| **发起研究** | P0 | 输入查询，提交任务 |
| **进度展示** | P0 | 实时轮询任务状态 |
| **结果查看** | P0 | Markdown 渲染研究报告 |
| **历史记录** | P0 | 本地存储研究历史 |
| **推送通知** | P0 | 研究完成时通知用户 |
| **设置** | P1 | API 地址、模型选择 |
| **分享** | P1 | 分享研究报告 |
| **收藏** | P2 | 收藏重要研究 |

### 高级功能 (后续版本)

| 功能 | 优先级 | 说明 |
|------|--------|------|
| **离线缓存** | P2 | 缓存已查看的报告 |
| **语音输入** | P2 | Siri/语音识别输入查询 |
| **小组件** | P3 | 桌面 Widget 快速查询 |
| **Siri 快捷指令** | P3 | "Hey Siri, 研究..." |
| **多语言** | P3 | 中英文切换 |

---

## 四、技术栈选型

### 核心技术

```json
{
  "framework": "React Native 0.73+",
  "language": "TypeScript",
  "navigation": "React Navigation 6",
  "state_management": "Zustand (轻量) 或 Redux Toolkit",
  "http_client": "Axios",
  "storage": "@react-native-async-storage/async-storage",
  "markdown": "react-native-markdown-display",
  "push_notification": "@react-native-firebase/messaging",
  "ui_components": "React Native Paper 或 NativeBase"
}
```

### 开发工具

```
• IDE: VS Code 或 Xcode
• 调试: React Native Debugger / Flipper
• 构建: Xcode (iOS), Android Studio (Android)
• 版本控制: Git
• CI/CD: Fastlane + GitHub Actions (可选)
```

---

## 五、App 页面设计

### 1. 首页 (Home Screen)

```
┌─────────────────────────────┐
│  MiroThinker          [⚙️]  │
├─────────────────────────────┤
│                             │
│  🔍 深度研究助手             │
│                             │
│  ┌─────────────────────┐   │
│  │ 输入研究问题...      │   │
│  │                     │   │
│  │                     │   │
│  └─────────────────────┘   │
│                             │
│  快捷选项:                   │
│  [技术趋势] [市场分析]       │
│  [学术研究] [竞品分析]       │
│                             │
│  ┌─────────────────────┐   │
│  │   🚀 开始研究        │   │
│  └─────────────────────┘   │
│                             │
│  最近研究:                   │
│  • AI 最新进展 - 完成 ✅    │
│  • 区块链应用 - 进行中 ⏳   │
│  • 市场趋势 - 失败 ❌       │
│                             │
└─────────────────────────────┘
```

### 2. 研究详情 (Result Screen)

```
┌─────────────────────────────┐
│  [<] 研究结果         [📤]  │
├─────────────────────────────┤
│                             │
│  # AI 市场分析报告           │
│                             │
│  ## 执行摘要                 │
│  AI 市场正在快速增长...      │
│                             │
│  ## 研究发现                 │
│  ### 市场规模                 │
│  - 2024年达到 $500亿         │
│  - 预计 2025年增长 30%       │
│                             │
│  ## 数据来源                 │
│  - Reuters (权威)            │
│  - Bloomberg (可靠)          │
│                             │
│  ───────────────────────    │
│  质量评分: 85/100 🏆         │
│  领域: 技术科技              │
│  用时: 3分42秒               │
│                             │
└─────────────────────────────┘
```

### 3. 设置页 (Settings Screen)

```
┌─────────────────────────────┐
│  设置                        │
├─────────────────────────────┤
│                             │
│  API 配置                     │
│  ┌─────────────────────┐   │
│  │ 服务器地址           │   │
│  │ https://your-server  │   │
│  └─────────────────────┘   │
│                             │
│  研究设置                     │
│  ┌─────────────────────┐   │
│  │ 默认模型             │   │
│  │ Qwen-Plus ▼         │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ 最大轮数             │   │
│  │ 100                 │   │
│  └─────────────────────┘   │
│                             │
│  通知设置                     │
│  [✓] 研究完成通知            │
│  [✓] 每日提醒               │
│                             │
│  关于                        │
│  版本: 1.0.0                 │
│                             │
└─────────────────────────────┘
```

---

## 六、API 集成

### 已有 API 端点 (直接使用)

| 端点 | 方法 | 用途 | App 中使用场景 |
|------|------|------|---------------|
| `/api/research` | POST | 提交研究任务 | 首页表单提交 |
| `/api/research/{id}` | GET | 查询任务状态 | 轮询进度、推送通知 |
| `/api/health` | GET | 健康检查 | App 启动时检查连接 |
| `/api/status` | GET | 系统状态 | 设置页显示 |

### 需要新增的 API (可选)

| 端点 | 方法 | 用途 | 说明 |
|------|------|------|------|
| `/api/user/register` | POST | 用户注册 | 如需多用户支持 |
| `/api/user/login` | POST | 用户登录 | 如需认证 |
| `/api/history` | GET | 获取历史列表 | 服务端历史 (替代本地) |
| `/api/research/{id}/share` | POST | 生成分享链接 | 分享功能 |

---

## 七、开发步骤

### 阶段一: 环境搭建 (1-2 天)

```bash
# 1. 安装开发环境
npm install -g react-native-cli
# 或使用 Expo (更简单)
npm install -g expo-cli

# 2. 创建项目
npx react-native init MiroThinkerApp --template react-native-template-typescript
# 或使用 Expo
npx create-expo-app MiroThinkerApp --template

# 3. 安装依赖
cd MiroThinkerApp
npm install axios zustand @react-navigation/native react-native-markdown-display
npm install @react-native-async-storage/async-storage
npm install @react-navigation/stack @react-navigation/bottom-tabs
```

### 阶段二: 核心功能开发 (3-5 天)

**文件结构**:
```
MiroThinkerApp/
├── src/
│   ├── screens/
│   │   ├── HomeScreen.tsx          # 首页
│   │   ├── ResultScreen.tsx        # 结果页
│   │   ├── HistoryScreen.tsx       # 历史页
│   │   └── SettingsScreen.tsx      # 设置页
│   ├── components/
│   │   ├── ResearchForm.tsx        # 研究表单组件
│   │   ├── ProgressBar.tsx         # 进度条
│   │   ├── MarkdownView.tsx        # Markdown 渲染
│   │   └── TaskCard.tsx            # 任务卡片
│   ├── services/
│   │   ├── api.ts                  # API 调用封装
│   │   └── storage.ts              # 本地存储
│   ├── store/
│   │   ├── useStore.ts             # 全局状态
│   │   └── types.ts                # 类型定义
│   └── utils/
│       ├── constants.ts            # 常量
│       └── helpers.ts              # 工具函数
├── App.tsx                         # 入口文件
└── package.json
```

**核心代码示例** (`services/api.ts`):

```typescript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://your-server.com'; // 你的服务器地址

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 发起研究任务
export const createResearchTask = async (query: string, options = {}) => {
  const response = await api.post('/api/research', {
    query,
    max_turns: 100,
    model: 'qwen-plus',
    ...options,
  });
  return response.data;
};

// 查询任务状态
export const getTaskStatus = async (taskId: string) => {
  const response = await api.get(`/api/research/${taskId}`);
  return response.data;
};

// 保存任务到本地历史
export const saveTaskToLocal = async (task: any) => {
  const history = await getTaskHistory();
  history.unshift(task);
  await AsyncStorage.setItem('research_history', JSON.stringify(history.slice(0, 50)));
};

// 获取本地历史
export const getTaskHistory = async () => {
  const history = await AsyncStorage.getItem('research_history');
  return history ? JSON.parse(history) : [];
};
```

### 阶段三: 推送通知 (1-2 天)

```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
```

**流程**:
1. App 启动时请求通知权限
2. 获取 Device Token 并保存
3. 研究任务完成时，服务器发送推送
4. 用户点击推送，打开结果页

**后端需添加** (可选):
```python
# 简单的推送通知 (使用 Firebase)
import firebase_admin
from firebase_admin import messaging

async def send_push_notification(device_token: str, task_id: str, title: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body='你的研究任务已完成，点击查看结果',
        ),
        data={'task_id': task_id},
        token=device_token,
    )
    response = messaging.send(message)
    return response
```

### 阶段四: 测试与优化 (2-3 天)

- 功能测试
- 性能优化
- 适配不同屏幕尺寸
- 测试网络异常处理

### 阶段五: 上架准备 (2-3 天)

- 准备 App Store 截图
- 编写 App 描述
- 申请 Apple Developer 账号 ($99/年)
- 提交审核

---

## 八、成本预估

### 开发成本

| 项目 | 时间 | 费用 (自研) | 费用 (外包) |
|------|------|------------|------------|
| 环境搭建 | 1-2 天 | - | ¥2,000 |
| 核心功能 | 3-5 天 | 你的时间 | ¥8,000-12,000 |
| 推送通知 | 1-2 天 | 你的时间 | ¥3,000 |
| 测试优化 | 2-3 天 | 你的时间 | ¥4,000 |
| 上架准备 | 2-3 天 | 你的时间 | ¥3,000 |
| **总计** | **9-15 天** | **你的时间** | **¥20,000-24,000** |

### 运营成本

| 项目 | 费用 | 说明 |
|------|------|------|
| Apple Developer | $99/年 (~¥700) | 必需 |
| 服务器 | ¥565/月 | 已有 |
| Firebase (推送) | 免费 | 免费额度足够 |
| **首年总计** | **~¥7,400** | 含服务器 |

---

## 九、快速启动方案 (Expo)

如果你想要**最快上线**，推荐使用 **Expo**:

```bash
# 1. 创建 Expo 项目
npx create-expo-app MiroThinkerApp --template

# 2. 安装依赖
cd MiroThinkerApp
npm install axios react-native-markdown-display @react-navigation/native

# 3. 开发核心页面
# (参考上面的代码示例)

# 4. 测试
npx expo start

# 5. 构建
eas build --platform ios

# 6. 提交
eas submit --platform ios
```

**Expo 优势**:
- ✅ 无需 Xcode 即可开发
- ✅ 内置推送通知支持
- ✅ 自动处理原生依赖
- ✅ OTA 更新 (无需重新审核)

---

## 十、替代方案: PWA (最快)

如果你**不想开发原生 App**，可以考虑 PWA:

```
PWA (渐进式 Web 应用) 方案:

优势:
• ✅ 无需 App Store 审核
• ✅ 开发成本最低 (前端改造即可)
• ✅ 跨平台 (iOS/Android/桌面)
• ✅ 支持推送通知
• ✅ 可添加到主屏幕

劣势:
• ❌ 性能略低于原生
• ❌ 部分原生功能不可用
• ❌ iOS 支持有限

实现步骤:
1. 添加 manifest.json
2. 添加 Service Worker
3. 配置推送通知
4. 部署到 HTTPS 服务器

开发时间: 1-2 天
成本: 几乎为 0
```

---

## 十一、推荐实施路径

### 路径一: 快速验证 (1 周)

```
Week 1:
├── Day 1-2: 前端改造成 PWA
├── Day 3-4: 测试推送通知
└── Day 5: 部署上线

成本: ¥700 (Apple Developer)
适合: 快速验证用户需求
```

### 路径二: 标准开发 (2-3 周)

```
Week 1: React Native 环境 + 核心功能
Week 2: 推送通知 + 测试
Week 3: 优化 + 上架

成本: ¥700 + 你的时间
适合: 正式发布
```

### 路径三: 完整开发 (1-2 月)

```
Week 1-2: React Native 完整功能
Week 3-4: 高级功能 (离线、语音、Widget)
Week 5-6: 测试 + 上架

成本: ¥700 + 你的时间 (或外包 ¥20,000+)
适合: 商业化运营
```

---

## 十二、下一步行动

### 立即可做

1. **确定开发方案** (React Native / Expo / PWA)
2. **准备开发环境** (Node.js, Xcode)
3. **设计 UI 原型** (Figma/Sketch)

### 一周内

4. **创建项目脚手架**
5. **开发核心页面**
6. **集成 API**

### 一个月内

7. **完成 MVP 功能**
8. **测试并上架**

---

## 总结

| 方案 | 开发时间 | 成本 | 推荐场景 |
|------|---------|------|---------|
| **PWA** | 1-2 天 | ¥0 | 快速验证 |
| **Expo** | 1-2 周 | ¥700/年 | 正式发布 ⭐ |
| **React Native** | 2-3 周 | ¥700/年 | 标准产品 |
| **Swift 原生** | 1-2 月 | ¥700/年 | 极致体验 |

**推荐**: 从 **Expo** 开始，快速上线验证需求，后续根据需要迁移到 React Native 或原生。

---

*需要我帮你搭建项目脚手架或编写核心代码吗？*
