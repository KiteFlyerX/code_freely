# 更新日志

## [未发布]

### Claude AI 增强 ✨

**文件**: `src/ai/claude.py`

#### 新增功能

- **流式响应重试机制**
  - 自动重试失败的 API 请求（默认最多 3 次）
  - 指数退避策略，避免频繁重试
  - 支持连接超时、API 错误等异常的重试

- **自定义端点支持**
  - 支持 `base_url` 参数配置自定义 API 端点
  - 兼容第三方中转服务
  - 可配置独立的超时时间（默认 5 分钟）

- **增强的流式工具调用**
  - 实时收集工具调用信息
  - 支持工具参数的增量解析
  - 提供详细的调试日志

- **改进的错误处理**
  - 区分可重试错误和致命错误
  - 详细的错误信息输出
  - 优雅的异常传播

#### 配置示例

```python
from src.ai import ClaudeAIFactory

# 使用官方端点
ai = ClaudeAIFactory.create(
    api_key="your_api_key",
    model="claude-sonnet-4-6"
)

# 使用自定义端点（中转服务）
ai = ClaudeAIFactory.create(
    api_key="your_api_key",
    model="claude-sonnet-4-6",
    base_url="https://your-proxy.com/v1",
    timeout=600,  # 10 分钟超时
    max_retries=5,  # 最多重试 5 次
    retry_delay=2.0  # 初始重试延迟 2 秒
)
```

#### 支持的模型

- `claude-opus-4-6` - 最强性能模型
- `claude-sonnet-4-6` - 平衡性能和速度
- `claude-haiku-4-5-20251001` - 快速响应模型
- `claude-3-5-sonnet-20241022` - 上一代 Sonnet
- `claude-3-5-haiku-20241022` - 上一代 Haiku

#### 技术细节

- **重试机制**: 使用指数退避算法，每次重试延迟时间翻倍
- **超时控制**: 使用 httpx.Timeout 精确控制连接和读取超时
- **流式处理**: 完全异步的流式响应处理，支持工具调用
- **Usage 追踪**: 自动记录每次请求的 token 使用情况

---

## v0.1.0 (2024-XX-XX)

### 新增功能

#### Bug 追踪服务 ✅

**文件**: `src/services/bug_service.py`

- 创建 Bug 报告（支持手动创建和从异常自动创建）
- 状态管理（待处理、处理中、已修复、已关闭）
- 关联代码修改和修复方案
- Bug 统计分析
- Bug 搜索

#### 代码审查服务 ✅

**文件**: `src/services/review_service.py`

- 创建和管理代码审查
- 提交审查意见（批准/请求修改）
- 行评论支持
- 评分系统（1-5 星）
- 审查者统计
- 合并检查

#### 知识库服务 ✅

**文件**: `src/services/knowledge_service.py`

- 知识条目创建和管理
- 自动分类（8 个预定义分类）
- 自动标签生成
- 全文搜索
- 从 Bug/审查/对话自动提取知识
- 相似条目推荐
- 访问统计

#### GUI 界面 ✅

**目录**: `src/gui/`

**框架**: PySide6 + PyQt-Fluent-Widgets

支持的视图：
- 聊天视图 - AI 对话界面，支持流式响应
- 历史视图 - 代码修改历史浏览
- Bug 视图 - Bug 追踪管理
- 审查视图 - 代码审查流程
- 知识库视图 - 知识浏览和搜索
- 设置视图 - 应用配置管理

#### 其他 AI 模型支持 ✅

**文件**:
- `src/ai/openai_impl.py` - OpenAI 实现
- `src/ai/deepseek_impl.py` - DeepSeek 实现

**支持的模型**:
- OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- DeepSeek: deepseek-chat, deepseek-coder, deepseek-reasoner

#### CLI 命令

```bash
# 启动图形界面
codetrace gui

# 向 AI 提问
codetrace ask "如何实现快速排序？"

# 查看对话历史
codetrace history

# 显示对话详情
codetrace show <conversation_id>

# 查看配置
codetrace config

# 设置 API 密钥
codetrace set-key

# 验证 API 密钥
codetrace verify
```

---

## 项目结构

```
CodeTraceAI/
├── src/
│   ├── ai/                    # AI 接口层
│   │   ├── base.py           # 抽象基类
│   │   ├── claude.py         # Claude 实现 ✨
│   │   ├── openai_impl.py    # OpenAI 实现
│   │   └── deepseek_impl.py  # DeepSeek 实现
│   ├── database/              # 数据库层
│   │   ├── manager.py        # 数据库管理
│   │   └── repositories.py   # 数据访问层
│   ├── models/                # 数据模型
│   │   └── database.py       # ORM 模型
│   ├── services/              # 业务服务层
│   │   ├── config_service.py
│   │   ├── conversation_service.py
│   │   ├── bug_service.py     # Bug 追踪服务
│   │   ├── review_service.py  # 代码审查服务
│   │   └── knowledge_service.py # 知识库服务
│   ├── vcs/                   # 版本控制
│   │   ├── base.py
│   │   └── git_impl.py
│   ├── gui/                   # GUI 界面
│   │   ├── main_window.py
│   │   └── views/
│   │       ├── chat_view.py
│   │       ├── history_view.py
│   │       ├── bug_view.py
│   │       ├── review_view.py
│   │       ├── knowledge_view.py
│   │       └── settings_view.py
│   └── utils/                 # 工具函数
├── codetrace/                 # CLI 入口
│   └── cli.py
├── config/                    # 配置模板
├── tests/                     # 测试
├── requirements.txt           # 依赖
├── pyproject.toml            # 项目配置
└── README.md
```

---

## 开发者信息

- **当前版本**: v0.1.0
- **Python 要求**: 3.9+
- **许可证**: MIT
- **仓库**: https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI.git
