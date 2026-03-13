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

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### CLI 模式

```bash
python -m codetrace.cli ask "编写一个排序函数"
```

### GUI 模式

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
└── requirements.txt  # 依赖
```
