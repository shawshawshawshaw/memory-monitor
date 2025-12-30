#!/usr/bin/env python3
"""macOS原生通知模块"""
import subprocess

def send_notification(title: str, message: str):
    """发送macOS原生通知"""
    subprocess.run([
        'terminal-notifier',
        '-title', title,
        '-message', message,
        '-sound', 'default'
    ], capture_output=True)
