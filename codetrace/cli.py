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

from src.services import conversation_service, config_service
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


if __name__ == "__main__":
    cli()
