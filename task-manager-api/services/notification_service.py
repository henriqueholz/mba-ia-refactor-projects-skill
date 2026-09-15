"""Notification service — SMTP credentials now come from config/env, not
hardcoded literals (fixes AP-SEC-01). If SMTP is not configured, sending is a
no-op instead of failing, so the app never blocks on notifications.
"""
import logging
import smtplib

from config.settings import Config
from utils.dates import utc_now

logger = logging.getLogger("notifications")


class NotificationService:
    def __init__(self):
        self.notifications = []
        self.host = Config.SMTP_HOST
        self.port = Config.SMTP_PORT
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.user or not self.password:
            logger.info("SMTP não configurado; e-mail para %s ignorado", to)
            return False
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, to, f"Subject: {subject}\n\n{body}")
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception as e:
            logger.error("Erro ao enviar email: %s", e)
            return False

    def notify_task_assigned(self, user, task):
        self.send_email(
            user.email,
            f"Nova task atribuída: {task.title}",
            f"Olá {user.name}, a task '{task.title}' foi atribuída a você.",
        )
        self.notifications.append(
            {"type": "task_assigned", "user_id": user.id, "task_id": task.id, "timestamp": utc_now()}
        )

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n["user_id"] == user_id]
