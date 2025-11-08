"""
分布式锁工具类
使用Redis实现分布式锁，用于并发控制
"""
import asyncio
import uuid
from typing import Optional
from app.database.redis_session import redis_connection


class DistributedLock:
    """
    Redis分布式锁实现
    使用SET命令的NX和EX选项实现
    """
    
    def __init__(self, key: str, timeout: int = 10, retry_times: int = 3, retry_delay: float = 0.1):
        """
        初始化分布式锁
        
        Args:
            key: 锁的键名
            timeout: 锁的超时时间（秒），防止死锁
            retry_times: 获取锁失败时的重试次数
            retry_delay: 重试延迟（秒）
        """
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.identifier = str(uuid.uuid4())  # 唯一标识符，用于释放锁时验证
    
    async def acquire(self) -> bool:
        """
        获取锁
        
        Returns:
            bool: 是否成功获取锁
        """
        for _ in range(self.retry_times):
            try:
                # redis.asyncio的set方法支持nx和ex参数
                result = await redis_connection.set(
                    self.key,
                    self.identifier,
                    nx=True,  # 只在键不存在时设置
                    ex=self.timeout  # 设置过期时间
                )
                
                if result:
                    return True
            except TypeError:
                # 如果set方法不支持nx/ex参数，使用setnx + expire
                try:
                    result = await redis_connection.setnx(self.key, self.identifier)
                    if result:
                        await redis_connection.expire(self.key, self.timeout)
                        return True
                except Exception:
                    pass
            except Exception:
                pass
            
            # 如果获取失败，等待一段时间后重试
            await asyncio.sleep(self.retry_delay)
        
        return False
    
    async def release(self) -> bool:
        """
        释放锁
        使用Lua脚本确保原子性：只有持有锁的进程才能释放锁
        
        Returns:
            bool: 是否成功释放锁
        """
        # Lua脚本：只有当锁的值等于我们的标识符时才删除
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            result = await redis_connection.eval(lua_script, 1, self.key, self.identifier)
            return result == 1
        except Exception:
            return False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not await self.acquire():
            raise Exception(f"Failed to acquire lock: {self.key}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.release()


async def with_distributed_lock(key: str, timeout: int = 10):
    """
    分布式锁装饰器/上下文管理器
    
    Usage:
        async with with_distributed_lock("product:123:stock", timeout=10):
            # 执行需要加锁的操作
            pass
    """
    return DistributedLock(key, timeout)

