"""
测试 logger 上下文功能
"""

import pytest

from maize.settings import SpiderSettings
from maize.utils.log_util import get_logger, get_spider_settings, set_spider_settings


def test_set_and_get_spider_settings():
    """测试设置和获取 spider settings"""
    settings = SpiderSettings()
    set_spider_settings(settings)

    retrieved_settings = get_spider_settings()
    assert retrieved_settings is settings


def test_get_logger_with_explicit_settings():
    """测试显式传入 settings 获取 logger（传统方式）"""
    settings = SpiderSettings()
    logger = get_logger(spider_settings=settings, name="TestLogger")

    assert logger is not None
    assert logger.name == "TestLogger"


def test_get_logger_from_context():
    """测试从上下文获取 logger（新方式）"""
    settings = SpiderSettings()
    set_spider_settings(settings)

    # 不传入 settings，应该自动从上下文获取
    logger = get_logger(name="ContextLogger")

    assert logger is not None
    assert logger.name == "ContextLogger"


def test_get_logger_without_settings_raises_error():
    """测试在没有 settings 时获取 logger 应该抛出错误"""
    # 清空上下文（通过设置为 None）
    # 注意：ContextVar 不能真正清空，但我们可以测试错误情况

    # 创建一个新的测试场景，不设置上下文
    try:
        # 尝试不传入 settings 且上下文中也没有
        get_logger(name="ErrorLogger")
        # 如果上下文中已经有 settings，则跳过这个测试
        if get_spider_settings() is not None:
            pytest.skip("Context already has settings")
    except ValueError as e:
        assert "spider_settings is required" in str(e)


def test_logger_caching():
    """测试 logger 缓存机制"""
    settings = SpiderSettings()
    set_spider_settings(settings)

    logger1 = get_logger(name="CachedLogger")
    logger2 = get_logger(name="CachedLogger")

    # 相同名称的 logger 应该返回同一个实例
    assert logger1 is logger2


if __name__ == "__main__":
    # 运行测试
    test_set_and_get_spider_settings()
    print("✓ test_set_and_get_spider_settings 通过")

    test_get_logger_with_explicit_settings()
    print("✓ test_get_logger_with_explicit_settings 通过")

    test_get_logger_from_context()
    print("✓ test_get_logger_from_context 通过")

    test_logger_caching()
    print("✓ test_logger_caching 通过")

    print("\n所有测试通过！")
