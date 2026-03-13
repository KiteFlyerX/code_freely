# CodeTraceAI 测试指南

本文档提供了完整的测试指南，包括环境准备、依赖安装、功能测试和故障排查。

## 目录

1. [环境准备](#环境准备)
2. [依赖安装](#依赖安装)
3. [单元测试](#单元测试)
4. [集成测试](#集成测试)
5. [CLI 功能测试](#cli-功能测试)
6. [GUI 功能测试](#gui-功能测试)
7. [API 测试](#api-测试)
8. [故障排查](#故障排查)

---

## 环境准备

### 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11、macOS、Linux
- **Git**: 用于版本控制集成

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

---

## 依赖安装

### 方式一：完整安装（含 GUI）

```bash
# 安装所有依赖
pip install -r requirements.txt
```

### 方式二：最小化安装（仅 CLI）

```bash
# 核心依赖
pip install sqlalchemy anthropic openai gitpython click rich

# 可选：GUI 依赖
pip install PySide6 PyQt-Fluent-Widgets
```

### 验证安装

```bash
# 检查关键包
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import anthropic; print('Anthropic OK')"
python -c "import openai; print('OpenAI OK')"
```

---

## 单元测试

### 运行核心测试

```bash
# 进入项目目录
cd CodeTraceAI

# 运行核心测试
python tests/test_core.py
```

**预期输出**:

```
Running CodeTraceAI tests...

--- Config Service ---
AI Provider: claude
AI Model: claude-sonnet-4-6
Config service: OK

--- Database ---
Database initialized
Found 0 config entries
Database: OK

--- VCS ---
Git repository detected, current branch: master
VCS: OK

--- AI Interface ---
ClaudeAI supported models: ['claude-opus-4-6', 'claude-sonnet-4-6', ...]
AI interface: OK

--- All tests completed ---
```

### 运行集成测试

```bash
python tests/test_integration.py
```

**预期输出**:

```
==================================================
CodeTraceAI 集成测试
==================================================

📊 测试数据库模块...
  ✅ 数据库初始化
  ✅ 数据库会话

🤖 测试 AI 接口模块...
  ✅ Claude AI 模型列表 (5 个)
  ✅ OpenAI 模型列表 (4 个)
  ✅ DeepSeek 模型列表 (3 个)

🔀 测试版本控制模块...
  ✅ Git 检测成功 (分支: master)
  ✅ Git 状态检查
  ✅ Git 文件变更检查 (0 个文件)

⚙️ 测试配置服务...
  ✅ 配置加载
  ✅ AI 配置结构
  ✅ 配置更新

💬 测试对话服务...
  ✅ 创建对话 (ID: 1)
  ✅ 对话列表 (1 个)
  ✅ 获取消息

🐛 测试 Bug 追踪服务...
  ✅ 创建 Bug (ID: 1)
  ✅ 获取 Bug 详情
  ✅ Bug 列表 (1 个)
  ✅ Bug 状态更新
  ✅ Bug 搜索

👁️ 测试代码审查服务...
  ✅ 创建审查 (ID: 1)
  ✅ 提交审查
  ✅ 审查摘要
  ✅ 合并检查

📚 测试知识库服务...
  ✅ 创建知识条目 (ID: 1)
  ✅ 获取知识条目
  ✅ 知识搜索
  ✅ 知识统计 (总数: 1)
  ✅ 分类获取
  ✅ 相似条目查找

🔗 测试服务集成...
  ✅ Bug 到知识提取
  ✅ 知识访问计数

==================================================
测试结果: 28/28 通过
==================================================
```

---

## CLI 功能测试

### 1. 配置测试

```bash
# 查看当前配置
codetrace config
```

**预期输出**:

```
当前配置:

AI 提供商: claude
AI 模型: claude-sonnet-4-6
温度: 0.7
最大 tokens: 4096
API 密钥: sk-ant-...
自动提交: True
创建临时分支: True
主题: auto
```

### 2. API 密钥设置测试

```bash
# 设置 API 密钥
codetrace set-key

# 验证密钥
codetrace verify
```

**预期输出** (密钥有效时):

```
API 密钥有效
```

### 3. AI 对话测试

```bash
# 简单提问
codetrace ask "Python 中如何反转一个列表?"

# 使用流式输出
codetrace ask "解释什么是递归" -s

# 指定模型
codetrace ask "介绍 Git" -m gpt-4o
```

### 4. 历史记录测试

```bash
# 查看对话历史
codetrace history

# 查看特定对话
codetrace show 1
```

### 5. 完整对话流程测试

```bash
# 1. 创建新对话
codetrace ask "帮我写一个快速排序函数"

# 2. 继续对话（使用对话 ID）
codetrace ask "能给代码添加注释吗？"

# 3. 查看历史
codetrace history

# 4. 查看详情
codetrace show 1
```

---

## GUI 功能测试

### 启动 GUI

```bash
codetrace gui
```

### GUI 测试清单

#### 1. AI 对话页面测试

- [ ] 页面正常加载
- [ ] 项目选择器显示当前目录
- [ ] 模型选择器包含所有支持模型
- [ ] 输入框可以输入文字
- [ ] 发送按钮正常工作
- [ ] AI 响应正常显示
- [ ] 新建对话按钮功能正常

#### 2. 历史记录页面测试

- [ ] 页面正常加载
- [ ] 表格显示代码修改历史
- [ ] 搜索框可以过滤结果
- [ ] 项目筛选器正常工作
- [ ] 刷新按钮更新数据

#### 3. Bug 追踪页面测试

- [ ] 页面正常加载
- [ ] Bug 列表正常显示
- [ ] 状态筛选器正常工作
- [ ] 新建 Bug 对话框打开
- [ ] 创建 Bug 成功
- [ ] 标记修复按钮功能正常

#### 4. 代码审查页面测试

- [ ] 页面正常加载
- [ ] 审查列表正常显示
- [ ] 新建审查功能正常
- [ ] 提交审查对话框打开
- [ ] 审查提交成功

#### 5. 知识库页面测试

- [ ] 页面正常加载
- [ ] 浏览标签页显示条目
- [ ] 搜索功能正常工作
- [ ] 统计标签页显示数据
- [ ] 新建条目功能正常

#### 6. 设置页面测试

- [ ] 页面正常加载
- [ ] AI 配置显示正确
- [ ] 提供商切换更新模型列表
- [ ] API 密钥验证功能正常
- [ ] 保存设置成功

---

## API 测试

### Python API 测试

创建测试文件 `test_api.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services import (
    bug_service, BugCreateInfo,
    review_service, ReviewCreateInfo, ReviewSubmitInfo, ReviewStatus,
    knowledge_service, KnowledgeCreateInfo,
    conversation_service
)

# 1. 测试对话服务
print("测试对话服务...")
conv_id = conversation_service.create_conversation("测试对话")
print(f"创建对话: {conv_id}")

# 2. 测试 Bug 服务
print("\n测试 Bug 服务...")
bug_id = bug_service.create_bug(BugCreateInfo(
    title="测试 Bug",
    description="API 测试 Bug",
))
print(f"创建 Bug: {bug_id}")

bug = bug_service.get_bug(bug_id)
print(f"Bug 状态: {bug.status}")

# 3. 测试知识库服务
print("\n测试知识库服务...")
entry_id = knowledge_service.create_entry(KnowledgeCreateInfo(
    title="API 测试知识",
    content="通过 API 创建的知识条目",
    tags=["api", "test"],
))
print(f"创建知识条目: {entry_id}")

# 4. 测试搜索
print("\n测试搜索...")
results = knowledge_service.search("API")
print(f"搜索结果: {len(results)} 个")

print("\n✅ API 测试完成")
```

运行测试:

```bash
python test_api.py
```

---

## 故障排查

### 常见问题

#### 1. ImportError: No module named 'xxx'

**问题**: 缺少依赖包

**解决**:
```bash
pip install xxx
# 或重新安装所有依赖
pip install -r requirements.txt
```

#### 2. API 密钥验证失败

**问题**: API 密钥未设置或无效

**解决**:
```bash
# 设置环境变量
export ANTHROPIC_API_KEY="your_key"
# 或
export OPENAI_API_KEY="your_key"

# 或通过命令设置
codetrace set-key
```

#### 3. 数据库错误

**问题**: 数据库初始化失败

**解决**:
```bash
# 删除旧数据库
rm -rf ~/.codetrace/

# 重新初始化
python -c "from src.database import init_database; init_database()"
```

#### 4. GUI 启动失败

**问题**: GUI 依赖未安装

**解决**:
```bash
pip install PySide6 PyQt-Fluent-Widgets
```

#### 5. Git 检测失败

**问题**: 当前目录不是 Git 仓库

**解决**:
```bash
# 初始化 Git 仓库
git init
git add .
git commit -m "Initial commit"
```

### 调试模式

启用详细日志:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

或设置环境变量:

```bash
export CODETRACE_DEBUG=1
```

---

## 性能测试

### 响应时间测试

```bash
# 测试 AI 响应时间
time codetrace ask "你好"
```

### 数据库查询测试

```python
import time
from src.services import conversation_service

start = time.time()
conversations = conversation_service.list_conversations(limit=100)
elapsed = time.time() - start

print(f"查询 {len(conversations)} 条记录，耗时 {elapsed:.2f} 秒")
```

---

## 持续集成

### GitHub Actions 示例

创建 `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python tests/test_core.py
      - run: python tests/test_integration.py
```

---

## 测试检查清单

### 发布前检查

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] CLI 命令正常工作
- [ ] GUI 界面正常加载
- [ ] 所有 AI 模型可用
- [ ] 数据库操作正常
- [ ] 版本控制集成正常
- [ ] 文档完整且准确
- [ ] 无已知严重 Bug

---

## 获取帮助

- 查看 README.md 获取基本信息
- 查看 CHANGELOG.md 了解新增功能
- 运行 `codetrace --help` 查看命令帮助
- 提交 Issue: https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI/issues
