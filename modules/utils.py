"""
工具函数库:缓存、重试、日志等通用功能
"""

import os
import pickle
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_flow.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# 缓存配置
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_api_call(cache_ttl_hours: int = 12):
    """
    装饰器:缓存 API 调用结果到本地文件

    Args:
        cache_ttl_hours: 缓存过期时间(小时)

    使用示例:
        @cache_api_call(cache_ttl_hours=12)
        def fetch_data(param1, param2):
            return api_call(param1, param2)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成唯一的缓存键
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")

            # 检查缓存是否存在且未过期
            if os.path.exists(cache_file):
                file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - file_time < timedelta(hours=cache_ttl_hours):
                    logger.info(f"缓存命中: {func.__name__}, 缓存文件: {cache_file}")
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                else:
                    logger.info(f"缓存过期: {func.__name__}, 重新获取数据")

            # 调用原函数
            logger.info(f"调用 API: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
            result = func(*args, **kwargs)

            # 保存到缓存
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                logger.info(f"缓存已保存: {cache_file}")
            except Exception as e:
                logger.warning(f"缓存保存失败: {e}")

            return result
        return wrapper
    return decorator


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError)),
    reraise=True
)
def robust_api_call(url: str, params: dict = None, headers: dict = None, timeout: int = 30) -> dict:
    """
    带重试机制的 API 调用

    Args:
        url: API 端点
        params: 查询参数
        headers: 请求头
        timeout: 超时时间(秒)

    Returns:
        API 响应的 JSON 数据

    Raises:
        requests.exceptions.RequestException: API 请求失败
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)

        # 处理限流
        if response.status_code == 429:
            logger.warning(f"API 限流: {url}, 等待后重试...")
            raise requests.exceptions.RequestException("Rate limit hit")

        # 处理服务器错误
        if response.status_code >= 500:
            logger.error(f"服务器错误 ({response.status_code}): {url}")
            raise requests.exceptions.RequestException(f"Server error: {response.status_code}")

        # 处理客户端错误
        if response.status_code >= 400:
            logger.error(f"客户端错误 ({response.status_code}): {url}, 响应: {response.text}")
            response.raise_for_status()

        logger.info(f"API 调用成功: {url}, 状态码: {response.status_code}")
        return response.json()

    except requests.exceptions.Timeout:
        logger.error(f"API 请求超时: {url}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"API 请求失败: {url}, 错误: {e}")
        raise


def clear_cache(older_than_hours: int = None):
    """
    清理缓存文件

    Args:
        older_than_hours: 清理多少小时前的缓存,None 表示清空所有缓存
    """
    if not os.path.exists(CACHE_DIR):
        logger.info("缓存目录不存在,无需清理")
        return

    count = 0
    for filename in os.listdir(CACHE_DIR):
        filepath = os.path.join(CACHE_DIR, filename)

        if not filename.endswith('.pkl'):
            continue

        # 如果指定了时间,只删除过期的
        if older_than_hours is not None:
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if datetime.now() - file_time < timedelta(hours=older_than_hours):
                continue

        try:
            os.remove(filepath)
            count += 1
        except Exception as e:
            logger.warning(f"删除缓存文件失败: {filepath}, 错误: {e}")

    logger.info(f"缓存清理完成,删除了 {count} 个文件")


def get_cache_info() -> dict:
    """
    获取缓存统计信息

    Returns:
        {"count": int, "total_size_mb": float, "oldest": str, "newest": str}
    """
    if not os.path.exists(CACHE_DIR):
        return {"count": 0, "total_size_mb": 0, "oldest": None, "newest": None}

    files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.pkl')]

    if not files:
        return {"count": 0, "total_size_mb": 0, "oldest": None, "newest": None}

    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)

    file_times = [os.path.getmtime(os.path.join(CACHE_DIR, f)) for f in files]
    oldest = datetime.fromtimestamp(min(file_times)).strftime('%Y-%m-%d %H:%M:%S')
    newest = datetime.fromtimestamp(max(file_times)).strftime('%Y-%m-%d %H:%M:%S')

    return {
        "count": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest": oldest,
        "newest": newest
    }


if __name__ == "__main__":
    # 测试代码
    @cache_api_call(cache_ttl_hours=1)
    def test_function(x, y):
        return x + y

    print(test_function(1, 2))
    print(test_function(1, 2))  # 应该命中缓存

    print("\n缓存信息:")
    print(get_cache_info())
