# Celery 异步任务队列配置指南

## 概述

本项目已集成 Celery 异步任务队列，用于处理耗时操作，如图片处理、邮件发送等。

## 安装依赖

```bash
pip install celery==5.4.0 Pillow==11.0.0
```

## 配置

在 `.env` 文件中添加 Celery 配置（可选，有默认值）：

```env
# Celery配置（可选，默认使用Redis）
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 启动 Celery Worker

### 开发环境

```bash
cd e-commerce
celery -A app.celery_app worker --loglevel=info
```

### 生产环境

```bash
# 使用多个worker进程
celery -A app.celery_app worker --loglevel=info --concurrency=4

# 后台运行
celery -A app.celery_app worker --loglevel=info --detach
```

### 使用 Supervisor 管理（推荐生产环境）

创建 `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery]
command=/path/to/venv/bin/celery -A app.celery_app worker --loglevel=info
directory=/path/to/e-commerce
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998
```

## 启动 Celery Beat（定时任务，如需要）

```bash
celery -A app.celery_app beat --loglevel=info
```

## 监控 Celery

### 使用 Flower（推荐）

```bash
pip install flower
celery -A app.celery_app flower
```

访问 http://localhost:5555 查看任务状态。

## 当前实现的异步任务

### 邮件任务

- `send_order_placement_email`: 发送订单创建邮件
- `send_payment_confirmation_email`: 发送支付确认邮件
- `send_password_recovery_email`: 发送密码重置邮件

### 图片处理任务

- `process_product_image`: 处理商品图片（生成缩略图）
- `process_user_avatar`: 处理用户头像（圆形裁剪、压缩）

## 降级处理

如果 Celery 不可用，系统会自动降级为同步处理，确保功能正常。

## 注意事项

1. 确保 Redis 服务正在运行
2. Celery worker 需要与 FastAPI 应用在同一环境中运行
3. 图片处理任务需要安装 Pillow 库
4. 邮件任务需要配置 SendGrid API Key

