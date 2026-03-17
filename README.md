# AI 编程辅助与知识沉淀工具

一款统一的 AI 编程接口工具，自动记录 AI 修改的代码、bug 提交和审查过程，形成团队知识库。

## 功能特性

- 多模型支持（Claude、DeepSeek、OpenAI）
- 自动记录代码修改和变更历史
- Bug 追踪与修复关联
- 代码审查流程管理
- 知识库构建与全文检索
- Git/SVN 版本控制集成

## 技术栈

- Python 3.9+
- SQLite + SQLAlchemy
- GitPython
- PySide6 (GUI)
- Click (CLI)

## 快速开始

### 1. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装测试依赖（可选）
pip install -r requirements-test.txt
```

### 2. 运行测试

```bash
# 方式1: 运行所有测试
python run_tests.py

# 方式2: 运行核心测试
python tests/test_core.py

# 方式3: 运行集成测试
python tests/test_integration.py

# 方式4: 使用 pytest（需要安装 pytest）
pytest tests/ -v
```

📖 **详细测试指南**: 查看 [TESTING.md](TESTING.md)

### 3. 使用应用

#### CLI 模式

```bash
python -m codetrace.cli ask "编写一个排序函数"
```

#### GUI 模式

```bash
python -m codetrace.gui
```

## 项目结构

```
CodeTraceAI/
├── src/
│   ├── ai/           # AI 接口抽象与实现
│   ├── database/     # 数据库层
│   ├── vcs/          # 版本控制集成
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑层
│   └── utils/        # 工具函数
├── config/           # 配置文件
├── tests/            # 测试
│   ├── test_core.py        # 核心功能测试
│   └── test_integration.py # 集成测试
├── run_tests.py      # 快速测试脚本
├── requirements.txt  # 核心依赖
├── requirements-test.txt  # 测试依赖
└── TESTING.md        # 测试指南
```

## 测试状态

✅ **核心功能**: 所有核心模块测试通过
✅ **集成测试**: 31/31 集成测试通过
✅ **数据库**: SQLite 数据库正常
✅ **版本控制**: Git 集成正常
✅ **AI 接口**: Claude/OpenAI/DeepSeek 接口正常

## 配置

在 `config/config.yaml` 中配置 AI API keys：

```yaml
ai:
  provider: claude  # 或 openai、deepseek
  model: claude-3-5-sonnet-20241022
  api_key: your-api-key-here
```

或使用环境变量：

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

## 开发

### 运行测试

```bash
# 运行所有测试
python run_tests.py

# 运行特定测试
python tests/test_core.py
python tests/test_integration.py

# 使用 pytest
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=html
```

### 代码风格

项目遵循 PEP 8 代码规范。

### 贡献

欢迎提交 Issue 和 Pull Request！

## 文档

- [TESTING.md](TESTING.md) - 详细测试指南
- [LICENSE](LICENSE) - 许可证

## 许可证

MIT License
