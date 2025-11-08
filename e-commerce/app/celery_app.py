"""
Celery异步任务队列配置
用于处理耗时操作，如图片处理、邮件发送等
"""
from celery import Celery
from app.config.settings import settings

# 创建Celery应用
celery_app = Celery(
    "ecommerce",
    broker=settings.CELERY_BROKER_URL,  # Redis作为消息代理
    backend=settings.CELERY_RESULT_BACKEND,  # Redis作为结果后端
    include=["app.tasks"]  # 包含任务模块
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 任务超时时间：30分钟
    task_soft_time_limit=25 * 60,  # 任务软超时：25分钟
    worker_prefetch_multiplier=1,  # 每个worker预取任务数
    worker_max_tasks_per_child=1000,  # 每个worker子进程最大任务数
)

