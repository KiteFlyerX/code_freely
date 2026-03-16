# CodeTraceAI 测试指南

本文档提供了完整的测试指南，包括环境准备、依赖安装、功能测试和故障排查。

## 目录

1. [环境准备](#环境准备)
2. [依赖安装](#依赖安装)
3. [单元测试](#单元测试)
4. [集成测试](#集成测试)
5. [提供商管理测试](#提供商管理测试)
6. [CC-Switch 集成测试](#cc-switch-集成测试)
7. [GUI 功能测试](#gui-功能测试)
8. [自动提交功能测试](#自动提交功能测试)
9. [打包测试](#打包测试)
10. [故障排查](#故障排查)

---

## 环境准备

### 系统要求

- **Python**: 3.9 或更高版本
- **操作系统**: Windows 10/11、macOS、Linux
- **Git**: 用于版本控制集成
- **CC-Switch** (可选): 用于导入 AI 提供商配置

### 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

### 检查 Git

```bash
git --version
```

---

## 依赖安装

### 完整安装（含 GUI）

```bash
# 安装所有依赖
pip install -r requirements.txt
```

### 核心依赖（仅 CLI）

```bash
pip install sqlalchemy anthropic openai gitpython click rich aiohttp
```

### GUI 依赖

```bash
pip install PySide6 PyQt-Fluent-Widgets
```

### 验证安装

```bash
# 检查关键包
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import anthropic; print('Anthropic OK')"
python -c "import openai; print('OpenAI OK')"
python -c "import PySide6; print('PySide6 OK')"
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

### 运行提供商服务测试

```bash
python test_provider_full.py
```

---

## 集成测试

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
  ✅ Git 文件变更检查

⚙️ 测试配置服务...
  ✅ 配置加载
  ✅ AI 配置结构
  ✅ 配置更新

💬 测试对话服务...
  ✅ 创建对话
  ✅ 对话列表
  ✅ 获取消息

🐛 测试 Bug 追踪服务...
  ✅ 创建 Bug
  ✅ 获取 Bug 详情
  ✅ Bug 列表
  ✅ Bug 状态更新
  ✅ Bug 搜索

👁️ 测试代码审查服务...
  ✅ 创建审查
  ✅ 提交审查
  ✅ 审查摘要
  ✅ 合并检查

📚 测试知识库服务...
  ✅ 创建知识条目
  ✅ 获取知识条目
  ✅ 知识搜索
  ✅ 知识统计
  ✅ 分类获取
  ✅ 相似条目查找

==================================================
测试结果: 28/28 通过
==================================================
```

---

## 提供商管理测试

### 1. 添加提供商测试

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services import ProviderConfig, ProviderType, provider_manager

# 创建 Claude 配置
claude_config = ProviderConfig(
    id="test_claude",
    name="测试 Claude",
    provider_type=ProviderType.CLAUDE,
    api_key="sk-ant-test-key",
    model="claude-sonnet-4-6",
    temperature=0.7,
    max_tokens=4096,
)

# 添加提供商
provider_manager.add_provider(claude_config)
print("✅ Claude 提供商已添加")

# 创建 OpenAI 配置
openai_config = ProviderConfig(
    id="test_openai",
    name="测试 OpenAI",
    provider_type=ProviderType.OPENAI,
    api_key="sk-test-key",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=4096,
)

provider_manager.add_provider(openai_config)
print("✅ OpenAI 提供商已添加")
```

### 2. 列出提供商测试

```python
# 列出所有提供商
providers = provider_manager.get_providers()
print(f"\n📋 提供商列表 ({len(providers)} 个):")
for p in providers:
    active = " [活动]" if p.is_active else ""
    print(f"  - {p.name} ({p.id}){active}")
```

### 3. 切换提供商测试

```python
# 切换到 Claude
if provider_manager.switch_provider("test_claude"):
    print("\n✅ 已切换到 Claude 提供商")

# 获取当前活动提供商
active = provider_manager.get_active_provider()
print(f"当前活动提供商: {active.name}")
```

### 4. 编辑/删除提供商测试

```python
# 编辑提供商
updated_config = ProviderConfig(
    id="test_claude",
    name="测试 Claude (已更新)",
    provider_type=ProviderType.CLAUDE,
    api_key="sk-ant-new-key",
    model="claude-opus-4-6",
)
provider_manager.update_provider("test_claude", updated_config)
print("✅ 提供商已更新")

# 删除提供商
if provider_manager.delete_provider("test_openai"):
    print("✅ OpenAI 提供商已删除")
```

### 5. 导入预设测试

```python
from src.services import PROVIDER_PRESETS

# 列出所有预设
print("\n📦 可用预设:")
for preset in PROVIDER_PRESETS:
    print(f"  - {preset.name} ({preset.id}) [{preset.category}]")

# 从预设添加
claude_preset = next(p for p in PROVIDER_PRESETS if p.id == "claude-default")
config = ProviderConfig(
    id=claude_preset.id,
    name=claude_preset.name,
    provider_type=claude_preset.config.provider_type,
    api_key="your-api-key-here",
    model=claude_preset.config.model,
)
provider_manager.add_provider(config)
print("✅ 已从预设添加 Claude 配置")
```

---

## CC-Switch 集成测试

### 1. 检测 CC-Switch 安装

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services import provider_manager
import os

# 检测 CC-Switch 数据库路径
ccswitch_paths = [
    Path.home() / ".cc-switch" / "cc-switch.db",
    Path(os.environ.get("APPDATA", "")) / "cc-switch" / "cc-switch.db",
    Path(os.environ.get("LOCALAPPDATA", "")) / "cc-switch" / "cc-switch.db",
]

print("🔍 检测 CC-Switch 安装:")
for path in ccswitch_paths:
    if path.exists():
        print(f"  ✅ 找到: {path}")
    else:
        print(f"  ❌ 未找到: {path}")
```

### 2. 从 CC-Switch 导入配置

```python
# 导入所有提供商
count = provider_manager.import_from_ccswitch()
print(f"\n📥 从 CC-Switch 导入了 {count} 个提供商配置")

# 列出导入的提供商
providers = provider_manager.get_providers()
print("\n当前提供商列表:")
for p in providers:
    if p.id.startswith("ccswitch_"):
        print(f"  - {p.name} ({p.id})")
```

### 3. 使用 CC-Switch 活跃提供商

```python
# 获取 CC-Switch 的活跃提供商
provider = provider_manager.get_ccswitch_active_provider()

if provider:
    print(f"\n✅ CC-Switch 活跃提供商: {provider.name}")
    print(f"   模型: {provider.model}")
    print(f"   端点: {provider.api_endpoint}")
else:
    print("\n⚠️ 未检测到 CC-Switch 配置")
```

---

## GUI 功能测试

### 启动 GUI

```bash
python start_simple_gui.py
```

### GUI 测试清单

#### 1. 聊天页面测试

- [ ] 页面正常加载
- [ ] 项目选择器显示当前目录
- [ ] CC-Switch 状态显示正确
- [ ] 模型标签显示 `[CC-Switch]` 标识
- [ ] 输入框可以输入文字
- [ ] 发送按钮正常工作
- [ ] AI 响应正常显示
- [ ] 新建对话按钮功能正常
- [ ] 自动提交复选框可用

#### 2. 设置页面测试

##### 提供商管理

- [ ] 提供商列表正常显示
- [ ] "从预设导入"按钮可用
- [ ] "手动添加"按钮可用
- [ ] "导出配置"按钮可用
- [ ] 选择提供商显示详情
- [ ] "设为活动"按钮功能正常
- [ ] "编辑"按钮功能正常
- [ ] "删除"按钮功能正常

##### AI 快速配置

- [ ] 提供商下拉框包含所有选项
- [ ] 切换提供商更新模型列表
- [ ] API 密钥输入框可用
- [ ] "显示"按钮切换密钥可见性
- [ ] "验证 API 密钥"按钮正常工作
- [ ] 保存设置成功

#### 3. 历史记录页面测试

- [ ] 页面正常加载
- [ ] 表格显示代码修改历史
- [ ] 搜索框可以过滤结果
- [ ] 项目筛选器正常工作
- [ ] 刷新按钮更新数据

#### 4. Bug 追踪页面测试

- [ ] 页面正常加载
- [ ] Bug 列表正常显示
- [ ] 状态筛选器正常工作
- [ ] 新建 Bug 对话框打开
- [ ] 创建 Bug 成功
- [ ] 标记修复按钮功能正常

#### 5. 代码审查页面测试

- [ ] 页面正常加载
- [ ] 审查列表正常显示
- [ ] 新建审查功能正常
- [ ] 提交审查对话框打开
- [ ] 审查提交成功

#### 6. 知识库页面测试

- [ ] 页面正常加载
- [ ] 浏览标签页显示条目
- [ ] 搜索功能正常工作
- [ ] 统计标签页显示数据
- [ ] 新建条目功能正常

---

## 自动提交功能测试

### 1. 测试自动提交对话框

```bash
# 启动 GUI
python start_simple_gui.py

# 测试步骤:
# 1. 进入聊天页面
# 2. 勾选"自动提交代码"
# 3. 发送代码修改请求
# 4. 应用代码时检查是否自动提交
```

### 2. 测试提交消息生成

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services import conversation_service

# 测试提交消息生成
changes = """
Modified Files:
  - src/gui/views/chat_view.py: 优先使用 CC-Switch 配置
  - src/services/provider_service.py: 添加 CC-Switch 集成

Changes:
  + 实现了 CC-Switch 配置优先读取
  + 添加了配置来源显示标识
"""

# 使用 AI 生成提交消息
message = conversation_service.generate_commit_message(changes)
print(f"生成的提交消息:\n{message}")
```

### 3. 测试完整自动提交流程

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.services import conversation_service

# 创建测试对话
conv_id = conversation_service.create_conversation("自动提交测试")

# 模拟代码修改
test_file = "test_auto_demo.py"
test_content = """
# 测试文件
def hello():
    print("Hello, World!")
"""

# 执行自动提交
result = conversation_service.auto_commit_changes(
    conversation_id=conv_id,
    files={test_file: test_content},
    auto_commit=True,
    push_to_remote=True,
)

if result.get("success"):
    print(f"✅ 自动提交成功")
    print(f"   提交 ID: {result.get('commit_id')}")
    print(f"   提交消息: {result.get('commit_msg')}")
    print(f"   已推送: {result.get('pushed')}")
else:
    print(f"❌ 自动提交失败: {result.get('error')}")
```

---

## 打包测试

### 1. 运行打包脚本

```bash
python build_exe.py
```

### 2. 验证打包结果

```bash
# 检查生成的文件
ls -lh dist/

# 检查绿色版目录
ls -lh dist/CodeTraceAI_Portable/

# 运行打包后的程序
./dist/CodeTraceAI_Portable/CodeTraceAI.exe
```

### 3. 测试绿色版功能

- [ ] exe 文件能正常启动
- [ ] 数据目录自动创建
- [ ] 日志目录自动创建
- [ ] 启动脚本工作正常
- [ ] 所有功能正常使用

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

#### 2. CC-Switch 检测失败

**问题**: 未找到 CC-Switch 配置文件

**解决**:
```bash
# 检查 CC-Switch 是否已安装
# Windows: 检查 %APPDATA%\cc-switch\ 或 %LOCALAPPDATA%\cc-switch\
# Linux/Mac: 检查 ~/.cc-switch/

# 如果使用的是其他路径，手动导入配置
```

#### 3. 提供商切换失败

**问题**: 无法切换提供商

**解决**:
```python
# 检查提供商是否存在
providers = provider_manager.get_providers()
for p in providers:
    print(f"{p.id}: {p.name}")

# 确保使用正确的提供商 ID
```

#### 4. API 密钥验证失败

**问题**: API 密钥未设置或无效

**解决**:
```bash
# 在 GUI 中设置 API 密钥
# 或通过代码设置
from src.services import ProviderConfig
config.api_key = "your-api-key"
provider_manager.update_provider(config.id, config)
```

#### 5. 数据库错误

**问题**: 数据库初始化失败

**解决**:
```bash
# 删除旧数据库
rm -rf ~/.codetrace/

# 重新初始化
python -c "from src.database import init_database; init_database()"
```

#### 6. GUI 启动失败

**问题**: GUI 依赖未安装

**解决**:
```bash
pip install PySide6 PyQt-Fluent-Widgets
```

#### 7. Git 检测失败

**问题**: 当前目录不是 Git 仓库

**解决**:
```bash
# 初始化 Git 仓库
git init
git add .
git commit -m "Initial commit"
```

#### 8. 自动提交失败

**问题**: Git 提交或推送失败

**解决**:
```bash
# 检查 Git 配置
git config user.name
git config user.email

# 设置 Git 配置
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 检查远程仓库
git remote -v
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

## 发布前检查清单

### 功能测试

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] CLI 命令正常工作
- [ ] GUI 界面正常加载
- [ ] 提供商管理功能正常
- [ ] CC-Switch 集成正常工作
- [ ] 自动提交功能正常

### AI 测试

- [ ] Claude 模型可用
- [ ] OpenAI 模型可用
- [ ] DeepSeek 模型可用
- [ ] 自定义端点可用

### 数据库测试

- [ ] 数据库初始化正常
- [ ] 数据库读写正常
- [ ] 数据库迁移正常

### 版本控制测试

- [ ] Git 检测正常
- [ ] Git 提交正常
- [ ] Git 推送正常
- [ ] 分支操作正常

### 打包测试

- [ ] 打包脚本运行成功
- [ ] exe 文件能正常启动
- [ ] 绿色版功能完整
- [ ] 安装包大小合理

### 文档测试

- [ ] README.md 完整准确
- [ ] TESTING.md 完整准确
- [ ] CHANGELOG.md 更新
- [ ] BUILD.md 完整准确

### 性能测试

- [ ] 启动时间 < 3 秒
- [ ] AI 响应时间合理
- [ ] 数据库查询 < 100ms
- [ ] 内存占用合理

### 安全测试

- [ ] API 密钥安全存储
- [ ] 无硬编码敏感信息
- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险

---

## 获取帮助

- 查看 README.md 获取基本信息
- 查看 CHANGELOG.md 了解新增功能
- 查看 BUILD.md 了解打包说明
- 查看 docs/PROVIDER_MANAGEMENT.md 了解提供商管理
- 运行 `codetrace --help` 查看命令帮助
- 提交 Issue: https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI/issues

---

## 附录

### 测试数据示例

#### 测试提供商配置

```python
test_providers = [
    {
        "id": "test_claude",
        "name": "测试 Claude",
        "type": "claude",
        "model": "claude-sonnet-4-6",
        "api_key": "sk-ant-test",
    },
    {
        "id": "test_openai",
        "name": "测试 OpenAI",
        "type": "openai",
        "model": "gpt-4o",
        "api_key": "sk-test",
    },
    {
        "id": "test_deepseek",
        "name": "测试 DeepSeek",
        "type": "deepseek",
        "model": "deepseek-chat",
        "api_key": "sk-test",
    },
]
```

#### 测试对话内容

```
用户: 帮我写一个快速排序函数
AI: 好的，这是快速排序的 Python 实现...

用户: 能给代码添加注释吗？
AI: 当然，这是添加了注释的版本...
```

#### 测试 Bug 数据

```python
test_bug = {
    "title": "登录页面响应慢",
    "description": "用户登录时页面加载超过 5 秒",
    "severity": "high",
    "priority": 1,
}
```

---

**文档版本**: 0.2.0
**最后更新**: 2026-03-16
