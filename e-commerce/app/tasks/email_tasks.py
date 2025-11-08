"""
邮件发送异步任务
"""
from app.celery_app import celery_app
from app.services.email_service import EmailService


@celery_app.task(name="send_order_placement_email")
def send_order_placement_email(email: str):
    """
    异步发送订单创建邮件
    
    Args:
        email: 收件人邮箱
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(EmailService.order_placement_message(email))
    except Exception as e:
        print(f"Failed to send order placement email to {email}: {e}")
        raise


@celery_app.task(name="send_payment_confirmation_email")
def send_payment_confirmation_email(email: str):
    """
    异步发送支付确认邮件
    
    Args:
        email: 收件人邮箱
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(EmailService.payment_confirmation_message(email))
    except Exception as e:
        print(f"Failed to send payment confirmation email to {email}: {e}")
        raise


@celery_app.task(name="send_password_recovery_email")
def send_password_recovery_email(email: str, token: str):
    """
    异步发送密码重置邮件
    
    Args:
        email: 收件人邮箱
        token: 重置令牌
    """
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(EmailService.password_recovery_email(email, token))
    except Exception as e:
        print(f"Failed to send password recovery email to {email}: {e}")
        raise

