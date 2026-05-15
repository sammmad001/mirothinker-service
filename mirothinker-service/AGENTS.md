# 新项目质量检查配置模板

## 使用说明

1. 将本文件复制为新项目的 `AGENTS.md`
2. 根据项目类型调整配置（Python/TypeScript/Go/Rust/Java）
3. 放置在新项目根目录
4. Qoder会自动读取并遵循配置

---

```markdown
# mirothinker-service AGENTS.md

## 项目概述

{简要描述项目功能和技术栈}

## 技术栈

- **语言**: Python 3.11 / TypeScript / Go 1.21 / Rust 1.70 / Java 17
- **框架**: FastAPI / Next.js / Gin / Actix / Spring Boot
- **测试**: Pytest / Vitest / Go test / Cargo test / JUnit 5
- **Lint工具**: Ruff / Biome / golangci-lint / Clippy / Checkstyle

## 目录结构

```
project-root/
├── src/              # 源代码
├── tests/            # 测试文件
├── docs/             # 文档
├── config/           # 配置文件
├── requirements.txt  # Python依赖 (或 package.json, go.mod, Cargo.toml)
└── AGENTS.md         # 本文件
```

---

## 质量检查自动触发配置

### 自动触发规则

当以下情况发生时，**必须**自动运行质量检查：

1. **代码修改后**：修改 `src/` 目录下的源文件
2. **功能开发完成后**：完成一个功能或修复bug，在会话结束前
3. **新增/修改测试文件后**：添加或修改测试文件
4. **用户明确要求时**：用户说"运行质量检查"或"检查代码质量"

### 质量检查技能

**主入口**：
- `project-quality-guard` - 质量检查调度器（自动检测项目类型并分发）

**专项技能**：
- `code-quality-auditor` - 代码质量审计（lint、类型检查、安全扫描）
- `functional-tester` - 功能测试验证（运行测试、检查覆盖率）
- `config-validator` - 配置文件验证（依赖、环境变量、CI/CD）
- `doc-consistency-checker` - 文档一致性检查

### 执行流程

```
代码修改 → project-quality-guard 自动检测
    ↓
识别项目类型和语言
    ↓
根据变更文件模式分发：
    ├─ src/** → code-quality-auditor + functional-tester (并行)
    ├─ tests/** → functional-tester
    ├─ docs/** → doc-consistency-checker
    └─ config/** → config-validator
    ↓
汇总报告 → 如有FAIL级别问题，阻断并提示修复
```

### 质量门禁标准

| 检查项 | 阈值 | 行为 |
|--------|------|------|
| 测试通过率 | 100% | FAIL: 阻断 |
| 代码覆盖率 | >= 80% | WARNING: 提示 |
| Critical安全问题 | 0 | FAIL: 阻断 |
| High安全问题 | 0 | FAIL: 阻断 |
| Lint错误 | 0 | FAIL: 阻断 |
| 类型检查错误 | 0 | FAIL: 阻断 |
| 代码复杂度超标 | 0个函数 | WARNING: 提示 |

### 手动触发命令

用户可以说：
- "运行质量检查" → 全量检查
- "检查最近变更" → 增量检查（最近commit）
- "检查这个文件" → 单文件检查
- "运行测试" → 仅运行functional-tester
- "检查文档" → 仅运行doc-consistency-checker

---

## 开发工作流

### 功能开发流程

1. 理解需求
2. 设计实现方案
3. 编写代码
4. **运行质量检查**（自动触发）
5. 修复发现的问题
6. 确认所有检查通过
7. 提交代码

### Bug修复流程

1. 重现问题
2. 定位根因
3. 编写修复代码
4. **运行质量检查**（自动触发）
5. 确认测试通过且无回归
6. 提交修复

### 代码重构流程

1. 确认重构目标
2. 运行基线质量检查（记录当前状态）
3. 执行重构
4. **运行质量检查**（自动触发）
5. 对比基线，确保无退化
6. 提交重构

---

## 项目特定配置

### Python项目

```toml
# pyproject.toml (质量检查相关配置)

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "C90"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.pytest.ini_options]
addopts = "--cov=. --cov-report=term-missing --cov-report=xml -v"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### TypeScript项目

```json
// package.json (质量检查相关配置)

{
  "scripts": {
    "lint": "biome check .",
    "type-check": "tsc --noEmit",
    "test": "vitest run --coverage",
    "test:watch": "vitest",
    "quality": "pnpm lint && pnpm type-check && pnpm test"
  },
  "devDependencies": {
    "@biomejs/biome": "^1.8.0",
    "typescript": "^5.5.0",
    "vitest": "^2.1.0",
    "@vitest/coverage-v8": "^2.1.0"
  }
}
```

### Go项目

```yaml
# .golangci.yml

run:
  timeout: 5m

linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gocyclo
    - gosec

linters-settings:
  gocyclo:
    min-complexity: 10
  gosec:
    severity: high

issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - errcheck
```

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 质量检查未自动触发 | 检查AGENTS.md是否存在，确认技能已安装 |
| 无法识别项目类型 | 确认项目根目录有标准配置文件 (package.json/pyproject.toml等) |
| 测试运行失败 | 确认测试依赖已安装 (pip install, npm install等) |
| 执行超时 | 检查是否有死循环或网络请求卡住 |
| 误报 | 在项目根目录添加 `.quality-ignore` 配置例外规则 |

---

## 持续改进

- 定期回顾质量门禁阈值是否合理
- 根据项目演进调整覆盖率要求
- 收集常见误报场景，优化配置
- 记录质量检查最佳实践

```

---

## 跨项目通用配置（可选）

如果你希望在**所有项目**中默认启用质量检查，可以创建全局配置：

### 方案：Qoder全局配置

创建文件 `~/.qoder/config.json`：

```json
{
  "quality": {
    "autoTrigger": {
      "onFileSave": true,
      "onCommit": true,
      "onSessionEnd": true
    },
    "skills": {
      "project-quality-guard": {
        "enabled": true,
        "triggerPatterns": [
          "src/**/*",
          "tests/**/*",
          "*.py",
          "*.ts",
          "*.js",
          "*.go",
          "*.rs"
        ]
      },
      "code-quality-auditor": {
        "enabled": true,
        "triggerPatterns": ["src/**/*"]
      },
      "functional-tester": {
        "enabled": true,
        "triggerPatterns": ["tests/**/*", "src/**/*"]
      }
    },
    "defaultGates": {
      "testPassRate": 100,
      "coverageThreshold": 80,
      "criticalSecurityIssues": 0,
      "lintErrors": 0
    }
  }
}
```

**注意**：此配置需要Qoder支持全局hooks功能。如果当前版本不支持，请使用项目级AGENTS.md方案。

---

## 快速开始清单

对于新项目：

- [ ] 1. 复制本模板为 `AGENTS.md`
- [ ] 2. 填写项目名称和技术栈
- [ ] 3. 根据语言选择对应配置（Python/TS/Go等）
- [ ] 4. 将AGENTS.md放置在项目根目录
- [ ] 5. 在首次开发时测试质量检查是否触发
- [ ] 6. 调整质量门禁阈值以适应项目需求

对于已有项目：

- [ ] 1. 创建 `AGENTS.md`（参考pkb-system/AGENTS.md）
- [ ] 2. 添加质量检查自动触发配置
- [ ] 3. 运行一次全量质量检查建立基线
- [ ] 4. 修复现有的FAIL级别问题
- [ ] 5. 配置质量门禁阈值

---

**最后更新**: 2026-05-13
**维护者**: 项目开发团队
