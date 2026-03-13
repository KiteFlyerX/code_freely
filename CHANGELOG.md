# 新增功能说明 v0.1.0

## Bug 追踪服务 ✅

**文件**: `src/services/bug_service.py`

### 功能列表

- 创建 Bug 报告（支持手动创建和从异常自动创建）
- 状态管理（待处理、处理中、已修复、已关闭）
- 关联代码修改和修复方案
- Bug 统计分析
- Bug 搜索

### 使用示例

```python
from src.services import bug_service, BugCreateInfo

# 创建 Bug
bug_id = bug_service.create_bug(BugCreateInfo(
    title="空指针异常",
    description="调用函数时出现 NoneType 错误",
    code_change_id=123,
))

# 从异常创建 Bug
try:
    risky_operation()
except Exception as e:
    bug_id = bug_service.create_bug_from_exception(
        exception=e,
        title="risky_operation 失败",
        code_change_id=123
    )

# 标记为已修复
bug_service.mark_fixed(bug_id, fix_description="添加了空值检查")

# 获取统计
stats = bug_service.get_bug_statistics()
```

---

## 代码审查服务 ✅

**文件**: `src/services/review_service.py`

### 功能列表

- 创建和管理代码审查
- 提交审查意见（批准/请求修改）
- 行评论支持
- 评分系统（1-5 星）
- 审查者统计
- 合并检查

### 使用示例

```python
from src.services import review_service, ReviewCreateInfo, ReviewSubmitInfo, ReviewStatus

# 创建审查
review_id = review_service.create_review(ReviewCreateInfo(
    code_change_id=456,
    reviewer="张三"
))

# 提交审查
review_service.submit_review(review_id, ReviewSubmitInfo(
    status=ReviewStatus.APPROVED,
    comment="代码质量良好，建议添加更多注释",
    rating=5,
    line_comments={23: "建议使用常量代替魔法数字"}
))

# 检查是否可以合并
can_merge, reason = review_service.can_merge(code_change_id=456)
```

---

## 知识库服务 ✅

**文件**: `src/services/knowledge_service.py`

### 功能列表

- 知识条目创建和管理
- 自动分类（8 个预定义分类）
- 自动标签生成
- 全文搜索
- 从 Bug/审查/对话自动提取知识
- 相似条目推荐
- 访问统计

### 预定义分类

- 最佳实践
- 常见问题
- 错误模式
- 设计模式
- 代码规范
- 工具使用
- 性能优化
- 安全建议

### 使用示例

```python
from src.services import knowledge_service, KnowledgeCreateInfo

# 创建知识条目
entry_id = knowledge_service.create_entry(KnowledgeCreateInfo(
    title="Python 字符串拼接最佳实践",
    content="使用 f-string 或 join() 方法...",
    category="最佳实践",
    tags=["python", "字符串", "性能"]
))

# 从 Bug 自动提取知识
knowledge_entry_id = knowledge_service.extract_from_bug(bug_id=789)

# 从审查提取知识
knowledge_entry_id = knowledge_service.extract_from_review(review_id=456)

# 从对话提取知识
knowledge_entry_id = knowledge_service.extract_from_conversation(
    message_id=123,
    title="如何使用装饰器"
)

# 搜索知识
results = knowledge_service.search(
    keyword="字符串拼接",
    category="最佳实践"
)

# 查找相似条目
similar = knowledge_service.find_similar(entry_id=123)
```

---

## GUI 界面 ✅

**目录**: `src/gui/`

**框架**: PySide6 + PyQt-Fluent-Widgets

### 视图列表

| 视图 | 文件 | 功能 |
|------|------|------|
| 聊天视图 | `chat_view.py` | AI 对话界面，支持流式响应 |
| 历史视图 | `history_view.py` | 代码修改历史浏览 |
| Bug 视图 | `bug_view.py` | Bug 追踪管理 |
| 审查视图 | `review_view.py` | 代码审查流程 |
| 知识库视图 | `knowledge_view.py` | 知识浏览和搜索 |
| 设置视图 | `settings_view.py` | 应用配置管理 |

### 启动 GUI

```bash
# 命令行启动
codetrace gui

# 或 Python 直接运行
python -m codetrace gui
```

---

## 其他 AI 模型支持 ✅

**文件**:
- `src/ai/openai_impl.py` - OpenAI 实现
- `src/ai/deepseek_impl.py` - DeepSeek 实现

### 支持的模型

#### Claude
- `claude-opus-4-6`
- `claude-sonnet-4-6`
- `claude-haiku-4-5-20251001`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

#### OpenAI
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

#### DeepSeek
- `deepseek-chat`
- `deepseek-coder`
- `deepseek-reasoner`

### 配置示例

```python
from src.services import config_service

# 切换到 OpenAI
config_service.update_ai_config(
    provider="openai",
    model="gpt-4o"
)

# 切换到 DeepSeek
config_service.update_ai_config(
    provider="deepseek",
    model="deepseek-chat"
)
```

---

## CLI 新增命令

```bash
# 启动图形界面
codetrace gui

# 向 AI 提问
codetrace ask "如何实现快速排序？"

# 查看对话历史
codetrace history
codetrace history -p ./myproject -n 50

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

## 安装依赖

### 完整安装（含 GUI）

```bash
pip install -r requirements.txt
```

### 仅 CLI 模式

```bash
pip install sqlalchemy anthropic openai gitpython click rich
```

---

## 快速开始

### 1. 设置 API 密钥

```bash
# 方式一：使用命令
codetrace set-key

# 方式二：设置环境变量
export ANTHROPIC_API_KEY="your_api_key"
# 或
export OPENAI_API_KEY="your_api_key"
```

### 2. 验证配置

```bash
codetrace verify
```

### 3. 启动应用

```bash
# GUI 模式
codetrace gui

# CLI 模式
codetrace ask "如何实现快速排序？"
```

---

## 项目结构

```
CodeTraceAI/
├── src/
│   ├── ai/                    # AI 接口层
│   │   ├── base.py           # 抽象基类
│   │   ├── claude.py         # Claude 实现
│   │   ├── openai_impl.py    # OpenAI 实现 ✨
│   │   └── deepseek_impl.py  # DeepSeek 实现 ✨
│   ├── database/              # 数据库层
│   │   ├── manager.py        # 数据库管理
│   │   └── repositories.py   # 数据访问层
│   ├── models/                # 数据模型
│   │   └── database.py       # ORM 模型
│   ├── services/              # 业务服务层
│   │   ├── config_service.py
│   │   ├── conversation_service.py
│   │   ├── bug_service.py     # Bug 追踪服务 ✨
│   │   ├── review_service.py  # 代码审查服务 ✨
│   │   └── knowledge_service.py # 知识库服务 ✨
│   ├── vcs/                   # 版本控制
│   │   ├── base.py
│   │   └── git_impl.py
│   ├── gui/                   # GUI 界面 ✨
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

- **版本**: v0.1.0
- **Python 要求**: 3.9+
- **许可证**: MIT
- **仓库**: https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI.git
