# CodeTraceAI 打包说明

## 快速开始

### Windows 用户
直接双击 `build.bat` 即可开始打包。

### 使用 Python 脚本
```bash
python build_exe.py
```

## 打包输出

打包成功后会生成以下文件：

```
dist/
├── CodeTraceAI.exe              # 主程序
└── CodeTraceAI_Portable/        # 绿色免安装版
    ├── CodeTraceAI.exe
    ├── 启动.bat
    ├── 使用说明.txt
    ├── data/                    # 数据目录
    └── logs/                    # 日志目录
```

## 系统要求

### 开发环境
- Python 3.8+
- PyInstaller 5.0+

### 运行环境（绿色版）
- Windows 10/11 64位
- 无需安装 Python

## 打包选项

### 单文件模式（默认）
- 所有依赖打包到一个 exe 中
- 文件较大（约 100-200MB）
- 便于分发

### 目录模式
- 修改 spec 文件，将 `console=False` 改为 `console=True`
- 可以显示调试信息

## 常见问题

### 打包失败
1. 确保已安装所有依赖: `pip install -r requirements.txt`
2. 确保已安装 PyInstaller: `pip install pyinstaller`
3. 检查是否有杀毒软件干扰（可能拦截打包过程）

### exe 运行失败
1. 检查是否缺少必要文件（如 src 目录）
2. 临时启用控制台模式查看错误信息
3. 检查日志文件

### 文件过大
- 使用 UPX 压缩（已启用）
- 考虑使用虚拟环境减少依赖
- 排除不需要的模块（在 spec 文件的 excludes 中添加）

## 高级配置

### 修改图标
在 spec 文件中设置：
```python
icon='path/to/icon.ico'
```

### 添加版本信息
在 spec 文件中添加：
```python
version='version.txt',
```

### 数字签名
在 spec 文件中设置：
```python
codesign_identity='Your Identity',
```
