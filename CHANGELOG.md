# Changelog

本项目所有重要变更均记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本管理遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 文档

- 新增 CHANGELOG.md、CONTRIBUTING.md
- 新增架构概览、FAQ/故障排查、示例索引页
- 新增 mkdocstrings 自动 API Reference
- 重设计文档首页
- README 增加 "Why maize"、Scrapy 对比、目录

## [0.5.0] - 2026-07-22

### 新增

- **Lite 轻量爬虫**（`maize.aio.lite`）—— 单依赖 aiohttp，构造函数即用
  - 内置请求去重（method+url+headers+params+data+json hash）
  - 深度控制（`max_depth`）、回调路由（`Request(callback=...)`）
  - `process_item` 钩子、优先级队列（`asyncio.PriorityQueue`）
  - 默认 UA、运行时统计（`crawler.stats`）、优雅关闭（SIGINT/SIGTERM）
  - 域名级并发限流（`per_domain_concurrency`）
  - 自定义重试策略（`should_retry`）、结构化 key=value 日志
- **中间件系统**（v0.4 引入，v0.5 文档完善）
  - 下载器中间件、爬虫中间件、管道中间件三层链
  - 内置 RetryMiddleware、UserAgentMiddleware、DefaultHeadersMiddleware、DepthMiddleware 等
- 枚举常量从 `maize` 顶层包导出：`SpiderDownloaderEnum`、`LogLevelEnum`、`PipelineEnum`、`Method`
- `get_logger` 放宽：`spider_settings=None` 时降级用默认格式创建 logger

### 修复

- LiteCrawler SIGINT 死锁：`await request_queue.join()` 在信号中断后永久阻塞，
  改为 sentinel + `asyncio.gather(*workers)` 方式
- `Request.hash` 缺失 `json` 字段，导致 POST+JSON 请求去重误杀不同 body
- `Request.__lt__` 文档方向写反：PriorityQueue 是 min-heap，数值越小越优先

### 变更

- Lite 爬虫 logger 从 `logging.getLogger` 迁移到 `maize.utils.log_util.get_logger`
- `LiteCrawler` 复用 `spider.logger`，避免重复 handler

## [0.4.0] - 2026-06

### 新增

- 中间件系统（下载器/爬虫/管道三层中间件链）
- 基于 Pydantic 重构 Item 和 BaseModel
- 基于 pydantic_settings 重构配置系统

### 变更

- 重构异步爬虫模块结构，分离 LiteCrawler 并简化 API
- 去除 `start_url` 功能，统一使用 `start_requests`
- 切换到 uv 作为构建工具

## [0.3.13] - 2026-04

### 新增

- RPA 爬虫支持并发
- Playwright/Patchright 通用基类抽取
- RPA 爬虫增加不加载资源类型列表（`skip_resource_types`）
- RPA 增加代理 IP 支持
- 代码生成功能
- 命令行工具增强

### 修复

- Response 返回格式不对的问题
- RPA 爬虫 download 方法返回值处理

## [0.3.8] - 2026-03

### 新增

- 爬虫暂停和恢复（`pause_spider` / `proceed_spider`）
- 爬虫状态上报增加重试
- Patchright 下载器

## [0.3.6] - 2026-02

### 新增

- 爬虫数据统计（采集、打印、上传联调）

## [0.3.5] - 2026-02

### 优化

- 响应编码的解析优化

## [0.3.2] - 2026-01

### 新增

- 最大重定向次数参数
- 是否重定向参数
- httpx 下载器 cookies 参数支持

### 修复

- httpx 下载器未支持 cookies 参数
- Windows 系统上的事件循环问题

## [0.3.0] - 2025-12

### 新增

- 支持 `RPA_ENDPOINT_URL` 环境变量
- 依赖拆分为 extras（`mysql`、`redis`、`rpa`、`all`）
- Request headers 函数参数
- 随机等待时间（`random_wait_time`）
- RPA 接口拦截（`url_regexes`）
- Response 增加 `source_response` 字段

## [0.2.10] - 2025-10

### 新增

- Request 增加 `json` 字段
- Playwright downloader session 模式支持 cookies

## [0.2.7] - 2025-09

### 新增

- TaskSpider 任务爬虫（分批获取任务、自动续航）
- RPA 爬虫
- RedisUtil 工具类
- 装饰器爬虫启动入口
- 分布式采集支持
- Pipeline 数据管道
- MySQL Pipeline
- 代理 IP 支持
- 请求/任务防丢机制
- Stealth JS 支持，升级 Playwright 版本

### 修复

- SingletonType 循环引用问题
- aioredis `TypeError: duplicate base class TimeoutError`

### 变更

- 重构项目目录结构

## [0.2.2] - 2025-07

### 新增

- 数据管道（Pipeline）系统
- MySQL Pipeline
- 代理 IP 支持

### 变更

- 调整 Item 数据表名字段，防止字段冲突
- 删除冗余目录结构

## [0.2.0] - 2025-06

### 新增

- 异步并发和任务处理
- 日志处理
- 错误重试
- Response cookies 处理
- 多进程采集
- 基础框架搭建
- 文档初始化、简介安装与快速上手
- CI workflows（多版本测试 3.8-3.12）
- 测试覆盖率

[Unreleased]: https://github.com/seehar/maize/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/seehar/maize/compare/v0.3.13...v0.5.0
[0.4.0]: https://github.com/seehar/maize/compare/v0.3.13...bb3df63
[0.3.13]: https://github.com/seehar/maize/compare/0.3.8...v0.3.13
[0.3.8]: https://github.com/seehar/maize/compare/0.3.7...0.3.8
[0.3.6]: https://github.com/seehar/maize/compare/0.3.5...0.3.6
[0.3.5]: https://github.com/seehar/maize/compare/0.3.4...0.3.5
[0.3.2]: https://github.com/seehar/maize/compare/0.3.1...0.3.2
[0.3.0]: https://github.com/seehar/maize/compare/0.2.10...0.3.0
[0.2.10]: https://github.com/seehar/maize/compare/0.2.9...0.2.10
[0.2.7]: https://github.com/seehar/maize/compare/0.2.3...0.2.7
[0.2.2]: https://github.com/seehar/maize/compare/0.2.1...0.2.2
[0.2.0]: https://github.com/seehar/maize/releases/tag/0.2.0
