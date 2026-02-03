"""
Dashboard Module - Real-time monitoring for RPA agents

Este módulo fornece interfaces visuais para monitoramento em tempo real
dos agentes RPA do MultiAgent Platform.
"""

from .web_monitor import dashboard, start_dashboard, DashboardManager

__all__ = ["dashboard", "start_dashboard", "DashboardManager"]
