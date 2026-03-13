"""
CLI 命令行入口
使用 Click 实现
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services import conversation_service, config_service, provider_manager, PROVIDER_PRESETS
from src.database import init_database
from src.utils import get_project_root, extract_code_blocks

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CodeTraceAI - AI 编程辅助与知识沉淀工具"""
    pass


@cli.command()
@click.argument("prompt", required=True)
@click.option("--project", "-p", help="项目路径", default=None)
@click.option("--stream", "-s", is_flag=True, help="使用流式输出")
@click.option("--model", "-m", help="指定模型", default=None)
def ask(prompt: str, project: Optional[str], stream: bool, model: Optional[str]):
    """
    向 AI 提问

    示例:
        codetrace ask "如何实现快速排序？"
        codetrace ask "解释这段代码" -p ./myproject
    """
    # 初始化数据库
    init_database()

    # 获取项目路径
    if project is None:
        project_path = str(get_project_root())
    else:
        project_path = project

    # 更新模型配置
    if model:
        config_service.update_ai_config(model=model)

    # 创建对话
    title = prompt[:50] + "..." if len(prompt) > 50 else prompt
    conversation_id = conversation_service.create_conversation(
        title=title,
        project_path=project_path,
    )

    console.print(f"[dim]项目路径: {project_path}[/dim]")
    console.print(f"[dim]对话 ID: {conversation_id}[/dim]\n")

    if stream:
        # 流式响应
        console.print(Panel(prompt, title="[bold]用户[/bold]"))

        async def stream_response():
            full_response = ""
            with console.status("[bold yellow]AI 思考中...", spinner="dots"):
                async for chunk in conversation_service.send_message_stream(
                    conversation_id, prompt
                ):
                    console.print(chunk, end="")
                    full_response += chunk

            console.print("\n")
            _display_response(full_response)

        asyncio.run(stream_response())
    else:
        # 普通响应
        with console.status("[bold yellow]AI 思考中...", spinner="dots"):
            message = asyncio.run(
                conversation_service.send_message(conversation_id, prompt)
            )

        _display_response(message.content)


def _display_response(content: str):
    """格式化显示响应"""
    # 检查是否包含代码块
    code_blocks = extract_code_blocks(content)

    if code_blocks:
        # 有代码块，分别显示
        console.print(Panel(content, title="[bold]AI 回复[/bold]", border_style="blue"))

        for i, code in enumerate(code_blocks, 1):
            console.print(f"\n[bold cyan]代码块 {i}:[/bold cyan]")
            # 尝试检测语言
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
    else:
        # 纯文本，作为 Markdown 显示
        md = Markdown(content)
        console.print(Panel(md, title="[bold]AI 回复[/bold]", border_style="blue"))


@cli.command()
@click.option("--project", "-p", help="项目路径", default=None)
@click.option("--limit", "-n", help="显示数量", default=20)
def history(project: Optional[str], limit: int):
    """
    查看对话历史

    示例:
        codetrace history
        codetrace history -p ./myproject -n 50
    """
    init_database()

    conversations = conversation_service.list_conversations(
        project_path=project, limit=limit
    )

    if not conversations:
        console.print("[yellow]没有找到对话记录[/yellow]")
        return

    for conv in conversations:
        console.print(f"\n[bold cyan]对话 {conv.id}:[/bold cyan] {conv.title}")
        console.print(f"  [dim]创建时间: {conv.created_at.strftime('%Y-%m-%d %H:%M')}[/dim]")
        if conv.project_path:
            console.print(f"  [dim]项目: {conv.project_path}[/dim]")


@cli.command()
@click.argument("conversation_id", type=int)
def show(conversation_id: int):
    """
    显示对话详情

    示例:
        codetrace show 1
    """
    init_database()

    messages = conversation_service.get_messages(conversation_id)

    if not messages:
        console.print(f"[yellow]对话 {conversation_id} 没有消息[/yellow]")
        return

    for msg in messages:
        if msg.role == "user":
            console.print(f"\n[bold green]用户:[/bold green] {msg.content}")
        else:
            console.print(f"\n[bold cyan]AI:[/bold cyan]")
            md = Markdown(msg.content)
            console.print(md)


@cli.command()
def config():
    """
    配置管理

    示例:
        codetrace config
    """
    cfg = config_service.get_config()

    console.print("\n[bold]当前配置:[/bold]\n")

    console.print(f"[cyan]AI 提供商:[/cyan] {cfg.ai.provider}")
    console.print(f"[cyan]模型:[/cyan] {cfg.ai.model}")
    console.print(f"[cyan]温度:[/cyan] {cfg.ai.temperature}")
    console.print(f"[cyan]最大 tokens:[/cyan] {cfg.ai.max_tokens}")

    masked_key = cfg.ai.api_key[:8] + "..." if cfg.ai.api_key else "(未设置)"
    console.print(f"[cyan]API 密钥:[/cyan] {masked_key}")

    console.print(f"\n[cyan]自动提交:[/cyan] {cfg.auto_commit}")
    console.print(f"[cyan]创建临时分支:[/cyan] {cfg.create_temp_branch}")
    console.print(f"[cyan]主题:[/cyan] {cfg.theme}")


@cli.command()
@click.option("--key", "-k", help="API 密钥", required=True, prompt=True, hide_input=True)
def set_key(key: str):
    """
    设置 API 密钥

    示例:
        codetrace set-key
    """
    cfg = config_service.get_config()
    provider = cfg.ai.provider

    config_service.save_api_key(provider, key)
    console.print(f"[green]已设置 {provider} 的 API 密钥[/green]")


@cli.command()
def verify():
    """
    验证 API 密钥

    示例:
        codetrace verify
    """
    with console.status("[bold yellow]验证中...", spinner="dots"):
        is_valid = conversation_service.validate_api_key()

    if is_valid:
        console.print("[green]API 密钥有效[/green]")
    else:
        console.print("[red]API 密钥无效，请检查配置[/red]")
        console.print("\n提示: 使用 [cyan]codetrace set-key[/cyan] 设置 API 密钥")


@cli.command()
def gui():
    """
    启动图形界面

    示例:
        codetrace gui
    """
    try:
        from src.gui import run_gui
        init_database()
        run_gui()
    except ImportError as e:
        console.print(f"[red]GUI 依赖未安装: {e}[/red]")
        console.print("\n请安装 GUI 依赖:")
        console.print("  pip install PySide6 PyQt-Fluent-Widgets")
    except Exception as e:
        console.print(f"[red]启动 GUI 失败: {e}[/red]")


# Provider 管理命令组
@cli.group()
def provider():
    """AI 提供商管理"""
    pass


@provider.command("list")
def provider_list():
    """
    列出所有提供商

    示例:
        codetrace provider list
    """
    init_database()

    providers = provider_manager.get_providers()
    active = provider_manager.get_active_provider()

    if not providers:
        console.print("[yellow]没有配置任何提供商[/yellow]")
        console.print("\n提示: 使用 [cyan]codetrace provider import[/cyan] 从预设导入")
        return

    console.print("\n[bold]已配置的提供商:[/bold]\n")

    for p in providers:
        # 标记当前活动的提供商
        status = "[green]√ 活动中[/green]" if active and p.id == active.id else ""
        enabled = "[green]已启用[/green]" if p.is_enabled else "[dim]已禁用[/dim]"

        console.print(f"[cyan]{p.name}[/cyan] ({p.id}) {status}")
        console.print(f"  类型: {p.provider_type.value}")
        console.print(f"  模型: {p.model}")
        console.print(f"  端点: {p.api_endpoint}")
        console.print(f"  状态: {enabled}")

        # 显示 API 密钥（部分隐藏）
        masked_key = p.api_key[:8] + "..." if p.api_key else "(未设置)"
        console.print(f"  API 密钥: {masked_key}")
        console.print("")


@provider.command("show")
@click.argument("provider_id")
def provider_show(provider_id: str):
    """
    显示提供商详情

    示例:
        codetrace provider show claude-official
    """
    init_database()

    providers = provider_manager.get_providers()
    provider = next((p for p in providers if p.id == provider_id), None)

    if not provider:
        console.print(f"[red]未找到提供商: {provider_id}[/red]")
        return

    console.print(f"\n[bold]{provider.name}[/bold]\n")
    console.print(f"[cyan]ID:[/cyan] {provider.id}")
    console.print(f"[cyan]类型:[/cyan] {provider.provider_type.value}")
    console.print(f"[cyan]模型:[/cyan] {provider.model}")
    console.print(f"[cyan]API 端点:[/cyan] {provider.api_endpoint}")
    console.print(f"[cyan]温度:[/cyan] {provider.temperature}")
    console.print(f"[cyan]最大 tokens:[/cyan] {provider.max_tokens}")
    console.print(f"[cyan]Top P:[/cyan] {provider.top_p}")

    if provider.proxy_url:
        console.print(f"[cyan]代理:[/cyan] {provider.proxy_url}")

    masked_key = provider.api_key[:8] + "..." if provider.api_key else "(未设置)"
    console.print(f"[cyan]API 密钥:[/cyan] {masked_key}")

    console.print(f"[cyan]已启用:[/cyan] {'是' if provider.is_enabled else '否'}")

    if provider.custom_params:
        console.print(f"\n[cyan]自定义参数:[/cyan]")
        for key, value in provider.custom_params.items():
            console.print(f"  {key}: {value}")


@provider.command("switch")
@click.argument("provider_id")
def provider_switch(provider_id: str):
    """
    切换活动提供商

    示例:
        codetrace provider switch claude-official
    """
    init_database()

    # 验证提供商存在
    providers = provider_manager.get_providers()
    provider = next((p for p in providers if p.id == provider_id), None)

    if not provider:
        console.print(f"[red]未找到提供商: {provider_id}[/red]")
        return

    if not provider.api_key:
        console.print(f"[yellow]警告: 该提供商未设置 API 密钥[/yellow]")

    if provider_manager.switch_provider(provider_id):
        console.print(f"[green]已切换到: {provider.name}[/green]")
    else:
        console.print("[red]切换失败[/red]")


@provider.command("add")
@click.option("--id", "-i", help="提供商 ID", prompt=True)
@click.option("--name", "-n", help="提供商名称", prompt=True)
@click.option("--type", "-t", help="提供商类型 (claude/openai/deepseek/custom)", prompt=True)
@click.option("--api-key", "-k", help="API 密钥", prompt=True, hide_input=True)
@click.option("--endpoint", "-e", help="API 端点", default="")
@click.option("--model", "-m", help="模型名称", default="")
def provider_add(id: str, name: str, type: str, api_key: str, endpoint: str, model: str):
    """
    添加新的提供商

    示例:
        codetrace provider add
    """
    init_database()

    from src.services.provider_service import ProviderConfig, ProviderType

    # 验证类型
    try:
        provider_type = ProviderType(type.lower())
    except ValueError:
        console.print(f"[red]无效的提供商类型: {type}[/red]")
        console.print("支持的类型: claude, openai, deepseek, custom")
        return

    # 创建配置
    config = ProviderConfig(
        id=id,
        name=name,
        provider_type=provider_type,
        api_key=api_key,
        api_endpoint=endpoint,
        model=model,
    )

    if provider_manager.add_provider(config):
        console.print(f"[green]已添加提供商: {name}[/green]")
    else:
        console.print("[red]添加失败[/red]")


@provider.command("delete")
@click.argument("provider_id")
@click.option("--confirm", "-y", is_flag=True, help="确认删除")
def provider_delete(provider_id: str, confirm: bool):
    """
    删除提供商

    示例:
        codetrace provider delete claude-official
        codetrace provider delete claude-official --confirm
    """
    init_database()

    # 检查是否为活动提供商
    active = provider_manager.get_active_provider()
    if active and active.id == provider_id:
        console.print("[red]无法删除当前活动的提供商[/red]")
        console.print("请先使用 [cyan]codetrace provider switch[/cyan] 切换到其他提供商")
        return

    if not confirm:
        if not click.confirm(f"确认删除提供商 '{provider_id}'?"):
            console.print("已取消")
            return

    if provider_manager.delete_provider(provider_id):
        console.print(f"[green]已删除提供商: {provider_id}[/green]")
    else:
        console.print("[red]删除失败[/red]")


@provider.command("update")
@click.argument("provider_id")
@click.option("--api-key", "-k", help="新的 API 密钥", prompt=True, hide_input=True)
@click.option("--model", "-m", help="新的模型名称", default=None)
@click.option("--endpoint", "-e", help="新的 API 端点", default=None)
def provider_update(provider_id: str, api_key: str, model: str, endpoint: str):
    """
    更新提供商配置

    示例:
        codetrace provider update claude-cleanup-temp
        codetrace provider update claude-official -k sk-ant-xxx -m claude-opus-4-6
    """
    init_database()

    from src.services.provider_service import ProviderConfig

    # 获取现有提供商
    providers = provider_manager.get_providers()
    existing = next((p for p in providers if p.id == provider_id), None)

    if not existing:
        console.print(f"[red]未找到提供商: {provider_id}[/red]")
        return

    # 更新配置
    config = ProviderConfig(
        id=existing.id,
        name=existing.name,
        provider_type=existing.provider_type,
        api_key=api_key,
        api_endpoint=endpoint if endpoint else existing.api_endpoint,
        model=model if model else existing.model,
        temperature=existing.temperature,
        max_tokens=existing.max_tokens,
        top_p=existing.top_p,
        proxy_url=existing.proxy_url,
        proxy_enabled=existing.proxy_enabled,
        is_active=existing.is_active,
        is_enabled=existing.is_enabled,
        custom_params=existing.custom_params,
    )

    if provider_manager.update_provider(provider_id, config):
        console.print(f"[green]已更新提供商: {config.name}[/green]")
        console.print(f"  API 密钥: {api_key[:8]}...")
        if model:
            console.print(f"  模型: {model}")
        if endpoint:
            console.print(f"  端点: {endpoint}")
    else:
        console.print("[red]更新失败[/red]")


@provider.command("presets")
def provider_presets():
    """
    列出所有可用的预设配置

    示例:
        codetrace provider presets
    """
    console.print("\n[bold]可用的预设配置:[/bold]\n")

    # 按类别分组
    categories = {}
    for preset in PROVIDER_PRESETS:
        if preset.category not in categories:
            categories[preset.category] = []
        categories[preset.category].append(preset)

    for category, presets in categories.items():
        console.print(f"[cyan]{category.upper()}:[/cyan]")
        for preset in presets:
            console.print(f"  [yellow]{preset.id}[/yellow]: {preset.name}")
            console.print(f"    {preset.description}")
        console.print("")


@provider.command("import")
@click.option("--preset", "-p", "preset_id", help="预设 ID", prompt=True)
@click.option("--api-key", "-k", help="API 密钥", prompt=True, hide_input=True)
@click.option("--name", "-n", help="自定义名称", default="")
def provider_import(preset_id: str, api_key: str, name: str):
    """
    从预设导入提供商

    示例:
        codetrace provider import
        codetrace provider import -p claude-official -k sk-ant-xxx
    """
    init_database()

    # 从预设导入
    config = provider_manager.import_from_preset(preset_id, api_key)

    if not config:
        console.print(f"[red]未找到预设: {preset_id}[/red]")
        console.print("\n提示: 使用 [cyan]codetrace provider presets[/cyan] 查看可用预设")
        return

    # 使用自定义名称
    if name:
        config.name = name
        config.id = f"{preset_id}-{name.lower().replace(' ', '-')}"
    # 否则直接使用预设 ID
    # config.id 已经在 preset 中设置了

    if provider_manager.add_provider(config):
        console.print(f"[green]已导入提供商: {config.name}[/green]")
        console.print(f"  ID: {config.id}")
        console.print(f"  类型: {config.provider_type.value}")
        console.print(f"  模型: {config.model}")
        console.print(f"\n[cyan]提示: 使用以下命令切换到此提供商:[/cyan]")
        console.print(f"  codetrace provider switch {config.id}")
    else:
        console.print("[red]导入失败[/red]")


@provider.command("export")
@click.option("--output", "-o", help="输出文件路径", default="providers.json")
def provider_export(output: str):
    """
    导出所有提供商配置到 JSON 文件

    示例:
        codetrace provider export
        codetrace provider export -o backup.json
    """
    init_database()

    json_data = provider_manager.export_providers()

    try:
        with open(output, "w", encoding="utf-8") as f:
            f.write(json_data)
        console.print(f"[green]已导出到: {output}[/green]")
    except Exception as e:
        console.print(f"[red]导出失败: {e}[/red]")


@provider.command("import-file")
@click.argument("file_path")
@click.option("--confirm", "-y", is_flag=True, help="确认导入")
def provider_import_file(file_path: str, confirm: bool):
    """
    从 JSON 文件导入提供商配置

    示例:
        codetrace provider import-file backup.json
    """
    init_database()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = f.read()
    except Exception as e:
        console.print(f"[red]读取文件失败: {e}[/red]")
        return

    if not confirm:
        if not click.confirm(f"确认从 '{file_path}' 导入提供商配置?"):
            console.print("已取消")
            return

    count = provider_manager.import_providers(json_data)
    if count > 0:
        console.print(f"[green]已导入 {count} 个提供商[/green]")
    else:
        console.print("[red]导入失败或没有有效的配置[/red]")


if __name__ == "__main__":
    cli()
