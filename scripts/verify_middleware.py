#!/usr/bin/env python3
"""
Middleware System Verification Script

This script verifies that all middleware components are properly installed
and can be imported successfully.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_base_imports():
    """Test that base middleware classes can be imported"""
    print("✓ Testing base middleware imports...")
    try:
        from maize.middlewares.base_middleware import (
            BaseMiddleware,
            DownloaderMiddleware,
            PipelineMiddleware,
            SpiderMiddleware,
        )

        assert all([BaseMiddleware, DownloaderMiddleware, PipelineMiddleware, SpiderMiddleware])
        print("  ✓ All base classes imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import base classes: {e}")
        return False


def test_manager_imports():
    """Test that middleware managers can be imported"""
    print("✓ Testing middleware manager imports...")
    try:
        from maize.middlewares.middleware_manager import (
            DownloaderMiddlewareManager,
            MiddlewareManager,
            PipelineMiddlewareManager,
            SpiderMiddlewareManager,
        )

        assert all([DownloaderMiddlewareManager, MiddlewareManager, PipelineMiddlewareManager, SpiderMiddlewareManager])
        print("  ✓ All managers imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import managers: {e}")
        return False


def test_downloader_middleware_imports():
    """Test that downloader middlewares can be imported"""
    print("✓ Testing downloader middleware imports...")
    try:
        from maize.middlewares.downloader import (
            DefaultHeadersMiddleware,
            RetryMiddleware,
            UserAgentMiddleware,
        )

        assert all([DefaultHeadersMiddleware, RetryMiddleware, UserAgentMiddleware])
        print("  ✓ All downloader middlewares imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import downloader middlewares: {e}")
        return False


def test_spider_middleware_imports():
    """Test that spider middlewares can be imported"""
    print("✓ Testing spider middleware imports...")
    try:
        from maize.middlewares.spider import (
            DepthMiddleware,
            HttpErrorMiddleware,
        )

        assert all([DepthMiddleware, HttpErrorMiddleware])
        print("  ✓ All spider middlewares imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import spider middlewares: {e}")
        return False


def test_pipeline_middleware_imports():
    """Test that pipeline middlewares can be imported"""
    print("✓ Testing pipeline middleware imports...")
    try:
        from maize.middlewares.pipeline import (
            ItemCleanerMiddleware,
            ItemValidationMiddleware,
        )

        assert all([ItemCleanerMiddleware, ItemValidationMiddleware])
        print("  ✓ All pipeline middlewares imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Failed to import pipeline middlewares: {e}")
        return False


def test_main_package_import():
    """Test that middlewares can be imported from main package"""
    print("✓ Testing main package imports...")
    try:
        from maize.middlewares import (
            BaseMiddleware,
            DepthMiddleware,
            DownloaderMiddleware,
            ItemValidationMiddleware,
            PipelineMiddleware,
            RetryMiddleware,
            SpiderMiddleware,
            UserAgentMiddleware,
        )

        assert all(
            [
                BaseMiddleware,
                DepthMiddleware,
                DownloaderMiddleware,
                ItemValidationMiddleware,
                PipelineMiddleware,
                RetryMiddleware,
                SpiderMiddleware,
                UserAgentMiddleware,
            ]
        )
        print("  ✓ Main package imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Failed main package import: {e}")
        return False


def test_settings_integration():
    """Test that middleware settings are available"""
    print("✓ Testing settings integration...")
    try:
        from maize.settings import SpiderSettings

        settings = SpiderSettings()
        assert hasattr(settings, "middleware"), "Settings missing middleware attribute"
        assert hasattr(settings.middleware, "downloader_middlewares")
        assert hasattr(settings.middleware, "spider_middlewares")
        assert hasattr(settings.middleware, "pipeline_middlewares")

        print("  ✓ Settings integration successful")
        return True
    except Exception as e:
        print(f"  ✗ Settings integration failed: {e}")
        return False


def test_middleware_instantiation():
    """Test that middlewares can be instantiated"""
    print("✓ Testing middleware instantiation...")
    try:
        from maize.middlewares.downloader import UserAgentMiddleware
        from maize.middlewares.pipeline import ItemValidationMiddleware
        from maize.middlewares.spider import DepthMiddleware

        # Test instantiation
        ua_middleware = UserAgentMiddleware()
        depth_middleware = DepthMiddleware()
        validation_middleware = ItemValidationMiddleware()

        # Test that they have required methods
        assert hasattr(ua_middleware, "process_request")
        assert hasattr(depth_middleware, "process_spider_output")
        assert hasattr(validation_middleware, "process_item_before")

        print("  ✓ Middleware instantiation successful")
        return True
    except Exception as e:
        print(f"  ✗ Middleware instantiation failed: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 80)
    print("Maize Middleware System Verification")
    print("=" * 80)
    print()

    tests = [
        test_base_imports,
        test_manager_imports,
        test_downloader_middleware_imports,
        test_spider_middleware_imports,
        test_pipeline_middleware_imports,
        test_main_package_import,
        test_settings_integration,
        test_middleware_instantiation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append(False)
        print()

    # Summary
    print("=" * 80)
    print("Verification Summary")
    print("=" * 80)
    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed! Middleware system is ready to use.")
        return 0
    print(f"✗ {total - passed} test(s) failed. Please check the errors above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
