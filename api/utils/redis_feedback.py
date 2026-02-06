# encoding: utf-8
"""
Redis 反馈工具
用于 Human-in-the-Loop 的异步反馈机制
"""
from config import REDIS_HOST, REDIS_PORT, REDIS_PASS, REDIS_DB
import redis
import json
import time
from typing import Optional, Dict, Any


class RedisFeedbackManager:
    """Redis 反馈管理器"""

    def __init__(self, redis_client=None, key_prefix='datachat:feedback'):
        """
        初始化

        Args:
            redis_client: Redis 客户端，如果为 None 则创建默认客户端
            key_prefix: Key 前缀
        """
        if redis_client is None:
            # 使用 ConnectionPool 创建 Redis 客户端
            pool = redis.ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASS,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_client = redis.Redis(connection_pool=pool)
        else:
            self.redis_client = redis_client

        self.key_prefix = key_prefix

    def _get_feedback_key(self, thread_id: str) -> str:
        """获取反馈 Key"""
        return f"{self.key_prefix}:{thread_id}"

    def _get_status_key(self, thread_id: str) -> str:
        """获取状态 Key"""
        return f"{self.key_prefix}:status:{thread_id}"

    def set_feedback(self, thread_id: str, feedback: str, expire: int = 1800):
        """
        设置用户反馈

        Args:
            thread_id: 线程 ID
            feedback: 用户反馈内容
            expire: 过期时间（秒），默认 30 分钟
        """
        key = self._get_feedback_key(thread_id)
        self.redis_client.setex(key, expire, feedback)

    def get_feedback(self, thread_id: str, delete: bool = True) -> Optional[str]:
        """
        获取用户反馈

        Args:
            thread_id: 线程 ID
            delete: 是否在获取后删除

        Returns:
            用户反馈内容，如果不存在返回 None
        """
        key = self._get_feedback_key(thread_id)

        if delete:
            # 获取并删除
            feedback = self.redis_client.get(key)
            if feedback:
                self.redis_client.delete(key)
            return feedback
        else:
            return self.redis_client.get(key)

    def wait_for_feedback(self, thread_id: str, timeout: int = 300, interval: int = 3) -> Optional[str]:
        """
        等待用户反馈（轮询）

        Args:
            thread_id: 线程 ID
            timeout: 超时时间（秒），默认 5 分钟
            interval: 轮询间隔（秒），默认 3 秒

        Returns:
            用户反馈内容，如果超时返回 None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            feedback = self.get_feedback(thread_id, delete=True)
            if feedback:
                return feedback

            # 等待下一次轮询
            time.sleep(interval)

        # 超时
        return None

    def set_status(self, thread_id: str, status: Dict[str, Any], expire: int = 1800):
        """
        设置执行状态

        Args:
            thread_id: 线程 ID
            status: 状态信息
            expire: 过期时间（秒），默认 30 分钟
        """
        key = self._get_status_key(thread_id)
        self.redis_client.setex(key, expire, json.dumps(status, ensure_ascii=False))

    def get_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        获取执行状态

        Args:
            thread_id: 线程 ID

        Returns:
            状态信息，如果不存在返回 None
        """
        key = self._get_status_key(thread_id)
        status_str = self.redis_client.get(key)

        if status_str:
            return json.loads(status_str)
        return None

    def delete_session(self, thread_id: str):
        """
        删除会话（清理所有相关 Key）

        Args:
            thread_id: 线程 ID
        """
        feedback_key = self._get_feedback_key(thread_id)
        status_key = self._get_status_key(thread_id)

        self.redis_client.delete(feedback_key, status_key)


# 全局实例（可选）
_feedback_manager = None


def get_feedback_manager() -> RedisFeedbackManager:
    """获取全局反馈管理器实例"""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = RedisFeedbackManager()
    return _feedback_manager
