# 爬虫目录结构重新设计方案

## 当前结构问题分析

1. **目录分散**：爬虫相关代码分散在 `maize/core/spider/` 和 `maize/spider/` 两个位置
2. **层次混乱**：接口定义和实现分离不够直观
3. **扩展性差**：难以优雅地扩展多线程爬虫
4. **命名不清晰**：lite/advanced 分类方式不够直观

## 新目录结构设计

```
maize/
├── spider/                          # 爬虫模块根目录
│   ├── __init__.py
│   ├── base/                        # 基础抽象层和公用组件
│   │   ├── __init__.py
│   │   ├── interfaces/              # 接口定义
│   │   │   ├── __init__.py
│   │   │   ├── spider_interface.py  # 爬虫基础接口
│   │   │   ├── downloader_interface.py # 下载器接口
│   │   │   ├── scheduler_interface.py # 调度器接口
│   │   │   ├── middleware_interface.py # 中间件接口
│   │   │   ├── pipeline_interface.py # 管道接口
│   │   │   └── lifecycle_interface.py # 生命周期接口
│   │   ├── mixins/                  # 混入类
│   │   │   ├── __init__.py
│   │   │   ├── stats_mixin.py       # 统计功能混入
│   │   │   └── lifecycle_mixin.py   # 生命周期管理混入
│   │   ├── spiders/                 # 公用爬虫基类
│   │   │   ├── __init__.py
│   │   │   ├── lite_spider_base.py  # 轻量级爬虫基类（同步/异步公用）
│   │   │   └── standard_spider_base.py # 标准爬虫基类（同步/异步公用）
│   │   ├── downloaders/             # 公用下载器基类和工具
│   │   │   ├── __init__.py
│   │   │   ├── downloader_base.py   # 下载器基类
│   │   │   ├── retry_handler.py     # 重试处理器（公用）
│   │   │   ├── proxy_manager.py     # 代理管理器（公用）
│   │   │   └── cookie_manager.py    # Cookie管理器（公用）
│   │   ├── schedulers/              # 公用调度器基类和工具
│   │   │   ├── __init__.py
│   │   │   ├── scheduler_base.py    # 调度器基类
│   │   │   ├── priority_queue.py    # 优先级队列（公用）
│   │   │   └── task_queue_base.py   # 任务队列基类（公用）
│   │   ├── middlewares/             # 公用中间件基类
│   │   │   ├── __init__.py
│   │   │   ├── middleware_base.py   # 中间件基类
│   │   │   ├── retry_base.py        # 重试中间件基类
│   │   │   └── user_agent_base.py   # User-Agent中间件基类
│   │   ├── pipelines/               # 公用管道基类
│   │   │   ├── __init__.py
│   │   │   ├── pipeline_base.py     # 管道基类
│   │   │   ├── validation_base.py   # 验证管道基类
│   │   │   └── storage_base.py      # 存储管道基类
│   │   └── exceptions.py            # 爬虫相关异常
│   │
│   ├── aio/                         # 异步爬虫实现 (asyncio)
│   │   ├── __init__.py
│   │   ├── lite/                    # 轻量级异步爬虫
│   │   │   ├── __init__.py
│   │   │   ├── spider.py           # LiteSpider实现（继承base.spiders.lite_spider_base）
│   │   │   ├── downloader/         # 异步轻量级下载器
│   │   │   │   ├── __init__.py
│   │   │   │   ├── httpx_downloader.py
│   │   │   │   └── aiohttp_downloader.py
│   │   │   ├── scheduler/          # 异步轻量级调度器
│   │   │   │   ├── __init__.py
│   │   │   │   └── async_simple_scheduler.py
│   │   │   ├── middleware/         # 异步轻量级中间件
│   │   │   │   ├── __init__.py
│   │   │   │   ├── async_retry_middleware.py
│   │   │   │   └── async_user_agent_middleware.py
│   │   │   ├── pipeline/           # 异步轻量级管道
│   │   │   │   ├── __init__.py
│   │   │   │   └── async_simple_pipeline.py
│   │   │   └── components/         # 其他异步组件
│   │   │       ├── __init__.py
│   │   │       ├── async_request_generator.py
│   │   │       └── async_response_parser.py
│   │   │
│   │   └── standard/                # 标准异步爬虫
│   │       ├── __init__.py
│   │       ├── spider.py           # StandardSpider实现（继承base.spiders.standard_spider_base）
│   │       ├── task_spider.py      # 异步任务爬虫
│   │       ├── downloader/         # 异步标准下载器
│   │       │   ├── __init__.py
│   │       │   ├── async_playwright_downloader.py
│   │       │   ├── async_patchright_downloader.py
│   │       │   └── async_browser_pool_downloader.py
│   │       ├── scheduler/          # 异步标准调度器
│   │       │   ├── __init__.py
│   │       │   ├── async_priority_scheduler.py
│   │       │   └── async_distributed_scheduler.py
│   │       ├── middleware/         # 异步标准中间件
│   │       │   ├── __init__.py
│   │       │   ├── async_proxy_middleware.py
│   │       │   ├── async_cache_middleware.py
│   │       │   └── async_rate_limit_middleware.py
│   │       ├── pipeline/           # 异步标准管道
│   │       │   ├── __init__.py
│   │       │   ├── async_batch_pipeline.py
│   │       │   └── async_distributed_pipeline.py
│   │       └── components/         # 其他异步组件
│   │           ├── __init__.py
│   │           ├── async_task_manager.py
│   │           └── async_resource_monitor.py
│   │
│   ├── sync/                        # 同步爬虫实现
│   │   ├── __init__.py
│   │   ├── lite/                    # 轻量级同步爬虫
│   │   │   ├── __init__.py
│   │   │   ├── spider.py           # SyncLiteSpider实现（继承base.spiders.lite_spider_base）
│   │   │   ├── downloader/         # 同步轻量级下载器
│   │   │   │   ├── __init__.py
│   │   │   │   ├── requests_downloader.py
│   │   │   │   └── urllib_downloader.py
│   │   │   ├── scheduler/          # 同步轻量级调度器
│   │   │   │   ├── __init__.py
│   │   │   │   └── sync_simple_scheduler.py
│   │   │   ├── middleware/         # 同步轻量级中间件
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sync_retry_middleware.py
│   │   │   │   └── sync_user_agent_middleware.py
│   │   │   ├── pipeline/           # 同步轻量级管道
│   │   │   │   ├── __init__.py
│   │   │   │   └── sync_simple_pipeline.py
│   │   │   └── components/         # 其他同步组件
│   │   │       ├── __init__.py
│   │   │       ├── sync_request_generator.py
│   │   │       └── sync_response_parser.py
│   │   │
│   │   └── standard/                # 标准同步爬虫
│   │       ├── __init__.py
│   │       ├── spider.py           # SyncStandardSpider实现（继承base.spiders.standard_spider_base）
│   │       ├── task_spider.py      # 同步任务爬虫
│   │       ├── downloader/         # 同步标准下载器
│   │       │   ├── __init__.py
│   │       │   ├── sync_playwright_downloader.py
│   │       │   ├── sync_patchright_downloader.py
│   │       │   └── sync_browser_pool_downloader.py
│   │       ├── scheduler/          # 同步标准调度器
│   │       │   ├── __init__.py
│   │       │   ├── sync_priority_scheduler.py
│   │       │   └── sync_distributed_scheduler.py
│   │       ├── middleware/         # 同步标准中间件
│   │       │   ├── __init__.py
│   │       │   ├── sync_proxy_middleware.py
│   │       │   ├── sync_cache_middleware.py
│   │       │   └── sync_rate_limit_middleware.py
│   │       ├── pipeline/           # 同步标准管道
│   │       │   ├── __init__.py
│   │       │   ├── sync_batch_pipeline.py
│   │       │   └── sync_distributed_pipeline.py
│   │       └── components/         # 其他同步组件
│   │           ├── __init__.py
│   │           ├── sync_task_manager.py
│   │           └── sync_resource_monitor.py
│   │
│   ├── factory/                     # 爬虫工厂
│   │   ├── __init__.py
│   │   ├── spider_factory.py        # 爬虫创建工厂
│   │   ├── downloader_factory.py    # 下载器工厂
│   │   ├── scheduler_factory.py     # 调度器工厂
│   │   ├── middleware_factory.py    # 中间件工厂
│   │   ├── pipeline_factory.py      # 管道工厂
│   │   └── registry.py              # 爬虫注册器
│   │
│   ├── utils/                       # 爬虫工具
│   │   ├── __init__.py
│   │   ├── decorators.py            # 装饰器
│   │   ├── validators.py            # 验证器
│   │   ├── helpers.py               # 辅助函数
│   │   ├── async_utils.py           # 异步工具函数
│   │   └── sync_utils.py            # 同步工具函数
│   │
│   └── templates/                   # 爬虫模板
│       ├── __init__.py
│       ├── base_templates.py        # 基础模板
│       ├── async_lite_template.py   # 异步轻量级爬虫模板
│       ├── async_standard_template.py # 异步标准爬虫模板
│       ├── sync_lite_template.py    # 同步轻量级爬虫模板
│       └── sync_standard_template.py # 同步标准爬虫模板
│
├── core/                            # 核心引擎模块
│   ├── __init__.py
│   ├── engine/                      # 引擎相关
│   │   ├── __init__.py
│   │   ├── base_engine.py           # 基础引擎抽象类
│   │   ├── async_engine.py          # 异步引擎（原engine.py重构）
│   │   ├── sync_engine.py           # 同步引擎（新增）
│   │   └── engine_factory.py        # 引擎工厂
│   │
│   ├── crawler/                     # 爬虫容器相关
│   │   ├── __init__.py
│   │   ├── crawler.py               # 爬虫容器（原core/crawler.py）
│   │   ├── async_crawler.py         # 异步爬虫容器
│   │   └── sync_crawler.py          # 同步爬虫容器
│   │
│   ├── scheduler/                   # 核心调度器
│   │   ├── __init__.py
│   │   ├── core_scheduler.py        # 核心调度器（原core/scheduler.py）
│   │   ├── async_scheduler.py       # 异步调度器
│   │   └── sync_scheduler.py        # 同步调度器
│   │
│   ├── processor/                   # 处理器相关
│   │   ├── __init__.py
│   │   ├── processor.py             # 处理器（原core/processor.py）
│   │   ├── async_processor.py       # 异步处理器
│   │   └── sync_processor.py        # 同步处理器
│   │
│   ├── stats/                       # 统计相关
│   │   ├── __init__.py
│   │   ├── stats_collector.py       # 统计收集器（原core/stats_collector.py）
│   │   └── stats_reporter.py        # 统计报告器
│   │
│   ├── task/                        # 任务管理相关
│   │   ├── __init__.py
│   │   ├── task_manager.py          # 任务管理器（原core/task_manager.py）
│   │   ├── async_task_manager.py    # 异步任务管理器
│   │   └── sync_task_manager.py     # 同步任务管理器
│   │
│   ├── runner/                      # 运行器相关
│   │   ├── __init__.py
│   │   ├── runner.py                # 基础运行器
│   │   ├── async_runner.py          # 异步运行器
│   │   └── sync_runner.py           # 同步运行器
│   │
│   └── registry/                    # 注册管理
│       ├── __init__.py
│       ├── spider_registry.py       # 爬虫注册管理
│       └── component_registry.py    # 组件注册管理
│
└── command/                         # 命令行工具
    ├── __init__.py
    ├── decorator_entry.py           # 装饰器入口（原core/decorator_entry.py）
    └── cli/                         # 命令行接口
        ├── __init__.py
        └── spider_cli.py            # 爬虫命令行工具
```

## 设计原则

### 1. 清晰的分层架构
- **base/**: 公用基础层，包含接口定义、基类和公用组件
- **aio/**: 异步爬虫实现（lite + standard）
- **sync/**: 同步爬虫实现（lite + standard）
- **factory/**: 工厂模式创建爬虫及组件实例
- **utils/**: 通用工具和辅助功能
- **templates/**: 爬虫开发模板

### 2. 公用组件与继承体系
- **base/spiders/**: lite和standard爬虫的公用基类（同步/异步公用）
- **base/downloaders/**: 下载器公用逻辑（重试、代理、Cookie管理等）
- **base/schedulers/**: 调度器公用逻辑（优先级队列、任务队列等）
- **base/middlewares/**: 中间件公用基类和逻辑
- **base/pipelines/**: 管道公用基类和逻辑

### 3. 专用组件实现
每个爬虫类型都有专用实现：
- **aio/lite/**: 异步轻量级实现（httpx/aiohttp + 简单调度）
- **aio/standard/**: 异步标准实现（playwright/patchright + 高级调度）
- **sync/lite/**: 同步轻量级实现（requests/urllib + 简单调度）
- **sync/standard/**: 同步标准实现（同步浏览器 + 高级调度）

### 4. 组件化生态系统
- **downloader/**: 专用下载器（lite: 轻量级HTTP客户端，standard: 浏览器引擎）
- **scheduler/**: 专用调度器（lite: 简单调度，standard: 优先级/分布式调度）
- **middleware/**: 专用中间件（lite: 基础功能，standard: 高级功能）
- **pipeline/**: 专用管道（lite: 简单处理，standard: 批量/分布式处理）

### 2. 易扩展性
- 通过接口抽象支持新的爬虫类型
- 工厂模式支持动态创建不同类型爬虫
- 组件化设计便于功能复用
- 混入类提供可选功能

### 3. 便于维护
- 按功能模块清晰分离
- 统一的命名规范
- 组件化设计降低耦合度
- 模板化开发提高一致性

### 4. 结构优雅
- 遵循单一职责原则
- 依赖关系清晰
- 支持插件式扩展
- 向后兼容现有代码

## 迁移计划

### 阶段1：重构现有结构
1. 创建新的目录结构
2. 将现有代码迁移到对应位置
3. 更新导入路径和依赖关系

### 阶段2：接口统一
1. 统一爬虫接口定义
2. 实现工厂模式
3. 添加混入类支持

### 阶段3：功能扩展
1. 实现同步爬虫框架
2. 添加更多组件支持
3. 完善模板系统

## 使用示例

### 创建轻量级异步爬虫
```python
from maize.spider.aio.lite.spider import LiteSpider
from maize.spider.aio.lite.downloader.httpx_downloader import HttpxDownloader
from maize.spider.aio.lite.scheduler.async_simple_scheduler import AsyncSimpleScheduler
from maize.spider.base.downloaders.retry_handler import RetryHandler  # 公用组件
from maize.spider.templates.async_lite_template import AsyncLiteTemplate

class MySpider(LiteSpider, AsyncLiteTemplate):
    name = "my_spider"

    def __init__(self):
        super().__init__()
        # 使用轻量级专用组件 + 公用组件
        self.downloader = HttpxDownloader()
        self.scheduler = AsyncSimpleScheduler()
        self.retry_handler = RetryHandler()  # 公用重试处理器

    async def parse(self, response):
        # 解析逻辑
        pass
```

### 创建标准异步爬虫
```python
from maize.spider.aio.standard.spider import StandardSpider
from maize.spider.aio.standard.downloader.async_playwright_downloader import AsyncPlaywrightDownloader
from maize.spider.aio.standard.scheduler.async_priority_scheduler import AsyncPriorityScheduler
from maize.spider.base.downloaders.proxy_manager import ProxyManager  # 公用组件
from maize.spider.templates.async_standard_template import AsyncStandardTemplate

class MyStandardSpider(StandardSpider, AsyncStandardTemplate):
    name = "my_standard_spider"

    def __init__(self):
        super().__init__()
        # 使用标准级专用组件 + 公用组件
        self.downloader = AsyncPlaywrightDownloader()
        self.scheduler = AsyncPriorityScheduler()
        self.proxy_manager = ProxyManager()  # 公用代理管理器

    async def parse(self, response):
        # 解析逻辑
        pass
```

### 创建轻量级同步爬虫
```python
from maize.spider.sync.lite.spider import SyncLiteSpider
from maize.spider.sync.lite.downloader.requests_downloader import RequestsDownloader
from maize.spider.sync.lite.scheduler.sync_simple_scheduler import SyncSimpleScheduler
from maize.spider.base.downloaders.retry_handler import RetryHandler  # 公用组件
from maize.spider.templates.sync_lite_template import SyncLiteTemplate

class MySyncSpider(SyncLiteSpider, SyncLiteTemplate):
    name = "my_sync_spider"

    def __init__(self):
        super().__init__()
        # 使用同步轻量级专用组件 + 公用组件
        self.downloader = RequestsDownloader()
        self.scheduler = SyncSimpleScheduler()
        self.retry_handler = RetryHandler()  # 同样的公用重试处理器

    def parse(self, response):
        # 解析逻辑
        pass
```

### 创建多线程爬虫（未来）
```python
from maize.spider.sync.threaded.spider import ThreadedSpider
from maize.spider.templates.sync_template import SyncSpiderTemplate

class MyThreadedSpider(ThreadedSpider, SyncSpiderTemplate):
    name = "my_threaded_spider"
    thread_count = 4

    def parse(self, response):
        # 解析逻辑
        pass
```

### 工厂模式创建爬虫生态
```python
from maize.spider.factory.spider_factory import SpiderFactory
from maize.spider.factory.downloader_factory import DownloaderFactory

# 创建异步轻量级爬虫生态
async_lite_ecosystem = SpiderFactory.create_ecosystem(
    spider_type="aio.lite",
    config={
        "spider": {"name": "my_async_lite_spider"},
        "downloader": {"type": "httpx", "timeout": 30},
        "scheduler": {"type": "async_simple", "max_concurrent": 10},
        "middleware": ["async_retry", "async_user_agent"],
        "pipeline": {"type": "async_simple"}
    }
)

# 创建异步标准爬虫生态
async_standard_ecosystem = SpiderFactory.create_ecosystem(
    spider_type="aio.standard",
    config={
        "spider": {"name": "my_async_standard_spider"},
        "downloader": {"type": "async_playwright", "headless": True},
        "scheduler": {"type": "async_priority", "max_concurrent": 5},
        "middleware": ["async_proxy", "async_cache", "async_rate_limit"],
        "pipeline": {"type": "async_batch", "batch_size": 100}
    }
)

# 创建同步轻量级爬虫生态
sync_lite_ecosystem = SpiderFactory.create_ecosystem(
    spider_type="sync.lite",
    config={
        "spider": {"name": "my_sync_lite_spider"},
        "downloader": {"type": "requests", "timeout": 30},
        "scheduler": {"type": "sync_simple", "max_concurrent": 10},
        "middleware": ["sync_retry", "sync_user_agent"],
        "pipeline": {"type": "sync_simple"}
    }
)

# 创建同步标准爬虫生态
sync_standard_ecosystem = SpiderFactory.create_ecosystem(
    spider_type="sync.standard",
    config={
        "spider": {"name": "my_sync_standard_spider"},
        "downloader": {"type": "sync_playwright", "headless": True},
        "scheduler": {"type": "sync_priority", "max_concurrent": 5},
        "middleware": ["sync_proxy", "sync_cache", "sync_rate_limit"],
        "pipeline": {"type": "sync_batch", "batch_size": 100}
    }
)

# 单独创建组件（可跨类型使用公用组件）
retry_handler = DownloaderFactory.create_component(
    component_type="retry_handler",
    config={"max_retries": 3, "backoff_factor": 2}
)

proxy_manager = DownloaderFactory.create_component(
    component_type="proxy_manager",
    config={"proxy_list": [...], "rotation_strategy": "round_robin"}
)
```

## 核心文件迁移方案

### 现有核心文件重新组织

#### 1. **引擎相关文件** (`core/engine/`)
```
原文件: core/engine.py → core/engine/async_engine.py
新增: core/engine/base_engine.py (抽象基类)
新增: core/engine/sync_engine.py (同步引擎)
新增: core/engine/engine_factory.py (引擎工厂)
```

#### 2. **爬虫容器文件** (`core/crawler/`)
```
原文件: core/crawler.py → core/crawler/crawler.py
重构: core/crawler/async_crawler.py (异步容器)
新增: core/crawler/sync_crawler.py (同步容器)
```

#### 3. **调度器文件** (`core/scheduler/`)
```
原文件: core/scheduler.py → core/scheduler/core_scheduler.py
重构: core/scheduler/async_scheduler.py (异步调度)
新增: core/scheduler/sync_scheduler.py (同步调度)
```

#### 4. **处理器文件** (`core/processor/`)
```
原文件: core/processor.py → core/processor/processor.py
重构: core/processor/async_processor.py (异步处理)
新增: core/processor/sync_processor.py (同步处理)
```

#### 5. **统计相关文件** (`core/stats/`)
```
原文件: core/stats_collector.py → core/stats/stats_collector.py
新增: core/stats/stats_reporter.py (统计报告)
```

#### 6. **任务管理文件** (`core/task/`)
```
原文件: core/task_manager.py → core/task/task_manager.py
重构: core/task/async_task_manager.py (异步任务)
新增: core/task/sync_task_manager.py (同步任务)
```

#### 7. **命令行文件** (`command/`)
```
原文件: core/decorator_entry.py → command/decorator_entry.py
新增: command/cli/spider_cli.py (命令行工具)
```
random
### 迁移原则

#### 1. **保持向后兼容**
- 保留原有文件的公共接口
- 通过适配器模式提供兼容性
- 逐步迁移，避免破坏性变更

#### 2. **异步/同步分离**
- 异步版本以 `async_` 前缀命名
- 同步版本以 `sync_` 前缀命名
- 公共逻辑提取到基类

#### 3. **职责分离**
- 引擎专注爬虫生命周期管理
- 调度器专注任务调度逻辑
- 处理器专注数据处理流程

### 使用示例

#### 异步爬虫使用

```python
from maize.core.engine.async_engine import AsyncEngine
from maize.aio.standard.crawler.crawler import AsyncCrawler

# 创建异步爬虫
crawler = AsyncCrawler(spider_cls, settings)
engine = AsyncEngine(crawler)
await engine.start()
```

#### 同步爬虫使用

```python
from maize.core.engine.sync_engine import SyncEngine
from maize.aio.standard.crawler.crawler import SyncCrawler

# 创建同步爬虫
crawler = SyncCrawler(spider_cls, settings)
engine = SyncEngine(crawler)
engine.start()
```

#### 工厂模式使用
```python
from maize.core.engine.engine_factory import EngineFactory

# 根据类型自动创建引擎
engine = EngineFactory.create_engine(
    engine_type="async",  # 或 "sync"
    crawler=crawler
)
```

## 优势总结

1. **清晰性**: 目录结构一目了然，功能模块清晰分离
2. **扩展性**: 支持异步、同步等多种爬虫类型，易于添加新功能
3. **维护性**: 模块化设计降低维护成本，组件复用提高开发效率
4. **优雅性**: 遵循设计模式，代码结构清晰，依赖关系明确
5. **一致性**: 统一的接口和命名规范，便于团队协作
6. **组件化生态**: 每种爬虫类型都有完整的专用组件生态，避免功能混杂
7. **性能优化**: lite组件专注于轻量高效，standard组件提供完整功能
8. **灵活组合**: 可以根据需求灵活选择和组合不同类型的组件
9. **公用组件复用**: base目录下的公用组件可被所有爬虫类型复用，减少代码重复
10. **继承体系清晰**: lite/standard爬虫继承各自的基类，同步/异步实现共享逻辑
11. **职责分离明确**: 公用逻辑放在base，专用逻辑放在具体实现，便于维护和扩展
12. **跨类型兼容**: 公用组件支持跨类型使用，提高组件的通用性和复用性
13. **核心模块化**: 引擎、调度器、处理器等核心功能独立模块化，便于单独维护和测试
14. **异步同步统一**: 通过统一的接口和工厂模式，异步和同步版本使用方式一致

这个设计既解决了当前结构的问题，又为未来的功能扩展提供了良好的基础。
