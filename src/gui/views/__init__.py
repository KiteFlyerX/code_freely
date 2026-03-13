"""
视图模块
"""
from .chat_view import ChatView
from .history_view import HistoryView
from .bug_view import BugView
from .review_view import ReviewView
from .knowledge_view import KnowledgeView
from .settings_view import SettingsView

__all__ = [
    "ChatView",
    "HistoryView",
    "BugView",
    "ReviewView",
    "KnowledgeView",
    "SettingsView",
]
