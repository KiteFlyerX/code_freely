# CodeTraceAI 测试指南

## 📋 测试概览

本项目提供了多种测试方式，从简单的导入测试到完整的集成测试。

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install -r requirements.txt
```

### 2. 运行所有测试

```bash
# 运行核心测试
python tests/test_core.py

# 运行集成测试（推荐）
python tests/test_integration.py
```

## 📁 测试文件说明

### 核心测试 (`tests/test_core.py`)

快速验证项目的核心功能模块是否正常工作。

**测试内容：**
- ✅ 配置服务 (Config Service)
- ✅ 数据库连接 (Database)
- ✅ 版本控制 (VCS - Git)
- ✅ AI 接口 (AI Interface)

**运行方式：**
```bash
python tests/test_core.py
```

**预期输出：**
```
Running CodeTraceAI tests...

--- Config Service ---
AI Provider: claude
AI Model: claude-3-5-sonnet-20241022
Config service: OK

--- Database ---
Database initialized
Found X config entries
Database: OK

--- VCS ---
Git repository detected, current branch: main
VCS: OK

--- AI Interface ---
ClaudeAI supported models: ['claude-3-5-sonnet-20241022', ...]
AI interface: OK

--- All tests completed ---
```

---

### 集成测试 (`tests/test_integration.py`)

完整的集成测试套件，测试所有服务和它们之间的协作。

**测试内容：**
- 🔹 数据库模块（初始化、会话）
- 🔹 AI 接口（Claude、OpenAI、DeepSeek）
- 🔹 版本控制（Git 检测、状态检查）
- 🔹 配置服务（加载、更新）
- 🔹 对话服务（创建、列表、消息）
- 🔹 Bug 追踪服务（创建、状态更新、搜索）
- 🔹 代码审查服务（创建、提交、合并检查）
- 🔹 知识库服务（创建、搜索、统计）
- 🔹 服务集成（Bug 提取知识、访问计数）

**运行方式：**
```bash
python tests/test_integration.py
```

**预期输出：**
```
==================================================
CodeTraceAI 集成测试
==================================================

[Database] 测试数据库模块...
  [PASS] 数据库初始化
  [PASS] 数据库会话

[AI] 测试 AI 接口模块...
  [PASS] Claude AI 模型列表 (X 个)
  [PASS] OpenAI 模型列表 (X 个)
  [PASS] DeepSeek 模型列表 (X 个)

[VCS] 测试版本控制模块...
  [PASS] Git 检测成功 (分支: main)
  [PASS] Git 状态检查
  [PASS] Git 文件变更检查 (X 个文件)

...

==================================================
测试结果: XX/XX 通过
==================================================
```

---

### 自动提交测试 (`test_auto_commit.py`)

测试 Git 自动提交功能。

**测试内容：**
- ✅ 检查自动提交配置
- ✅ Git 仓库检测
- ✅ 未提交更改检查
- ✅ 创建代码修改记录
- ✅ 模拟自动提交
- ✅ 验证提交结果
- ✅ 临时分支功能

**运行方式：**
```bash
python test_auto_commit.py
```

**注意事项：**
- ⚠️ 此测试会实际执行 Git 提交操作
- ⚠️ 建议在测试分支上运行
- ⚠️ 确保已配置 Git 用户信息

---

### 导入测试 (`test_import.py`)

测试所有模块是否能正常导入（用于检查依赖和导入路径）。

**测试内容：**
- ✅ 核心模块导入（ai、database、models、services、vcs）
- ✅ GUI 模块导入和窗口创建

**运行方式：**
```bash
python test_import.py
```

**注意事项：**
- 🖥️ 会打开 GUI 窗口
- 🖥️ 需要图形界面环境

---

### 其他测试文件

- `test_minimal_gui.py` - 最小化 GUI 测试
- `test_provider_full.py` - AI 提供者完整测试
- `test_provider_service.py` - AI 服务测试
- `test_auto_commit_demo.py` - 自动提交演示

## 🧪 使用 pytest 运行测试（可选）

如果你想使用 pytest 框架：

```bash
# 安装 pytest
pip install pytest pytest-cov

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_core.py -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 🔧 测试前准备

### 1. 配置 AI API Keys

在 `config/config.yaml` 中配置你的 AI API keys：

```yaml
ai:
  provider: claude  # 或 openai、deepseek
  model: claude-3-5-sonnet-20241022
  api_key: your-api-key-here
```

或在环境变量中设置：

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

### 2. 初始化数据库

```bash
python -c "from src.database import init_database; init_database()"
```

### 3. 检查 Git 仓库

确保当前目录是 Git 仓库：

```bash
git status
```

## 📊 测试最佳实践

### 1. 运行测试的顺序

```bash
# 1. 先运行导入测试（检查基础依赖）
python test_import.py

# 2. 然后运行核心测试（检查核心功能）
python tests/test_core.py

# 3. 最后运行集成测试（检查完整流程）
python tests/test_integration.py
```

### 2. 持续测试

在开发过程中，建议：

- 每次修改代码后运行相关测试
- 提交代码前运行完整测试套件
- 定期检查测试覆盖率

### 3. 调试测试

如果测试失败：

```bash
# 运行单个测试函数
python tests/test_core.py
# 在代码中添加断点或 print 语句调试

# 使用 pytest 的详细输出
pytest tests/test_core.py -v -s
```

## 🐛 常见问题

### Q1: 测试时报错 "ModuleNotFoundError"

**解决方案：**
```bash
# 确保在项目根目录运行
cd E:\workspaces\python\CodeTraceAI

# 检查 Python 路径
python -c "import sys; print(sys.path)"
```

### Q2: 数据库测试失败

**解决方案：**
```bash
# 删除现有数据库重新初始化
rm -f data/codetrace.db
python -c "from src.database import init_database; init_database()"
```

### Q3: Git 测试失败

**解决方案：**
```bash
# 检查 Git 配置
git config user.name
git config user.email

# 如果没有配置，设置一下
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Q4: AI 接口测试失败

**解决方案：**
- 检查 API key 是否正确配置
- 检查网络连接
- 某些测试只是验证模型列表，不需要实际调用 API

## 📈 查看测试结果

### 成功的测试

测试成功时会看到：
```
[PASS] 测试项名称
[OK] 所有测试通过!
```

### 失败的测试

测试失败时会看到：
```
[FAIL] 测试项名称: 错误详情
```

并会打印完整的错误堆栈。

## 🎯 下一步

测试通过后，你可以：

1. **运行应用程序**
   ```bash
   # CLI 模式
   python -m codetrace.cli ask "编写一个排序函数"

   # GUI 模式
   python -m codetrace.gui
   ```

2. **查看项目文档**
   - README.md - 项目概览
   - docs/ - 详细文档

3. **开始开发**
   - 查看 `src/` 目录下的源代码
   - 根据需求添加新功能

## 📝 总结

- 🚀 **快速测试**: `python tests/test_integration.py`
- 🔍 **单项测试**: 运行特定测试文件
- 🐛 **调试**: 使用 `-v` 参数查看详细输出
- ✅ **最佳实践**: 定期运行测试，确保代码质量

祝测试顺利！🎉
