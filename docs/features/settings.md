# 配置说明

maize 使用基于 Pydantic 的配置系统，提供了强类型检查和灵活的配置方式。

## 配置方式

maize 支持多种配置方式，按优先级从高到低排列：

1. **代码配置**（`custom_settings`）- 最高优先级
2. **SpiderSettings 对象**
3. **环境变量**
4. **.env 文件**
5. **YAML 配置文件**
6. **TOML 配置文件**
7. **settings.py 配置文件**
8. **默认配置** - 最低优先级

## 方式一：SpiderSettings 对象（推荐）

使用 `SpiderSettings` 对象进行配置，可以获得完整的类型提示和代码补全。

### 基础配置

```python
from maize import Spider, SpiderSettings


class MySpider(Spider):
    # ...爬虫实现...
    pass


if __name__ == "__main__":
    settings = SpiderSettings(
        project_name="我的爬虫项目",
        concurrency=10,
        log_level="INFO",
        downloader="maize.HTTPXDownloader"
    )

    MySpider().run(settings=settings)
```

### 嵌套配置

```python
from maize import SpiderSettings
from maize.settings.spider_settings import RequestSettings, PipelineSettings


settings = SpiderSettings(
    project_name="高级爬虫",
    concurrency=20,
    log_level="DEBUG",
)

# 配置请求参数
settings.request.verify_ssl = False
settings.request.request_timeout = 30
settings.request.max_retry_count = 3
settings.request.random_wait_time = (1, 3)  # 随机等待1-3秒

# 配置数据管道
settings.pipeline.pipelines = ["my_project.pipelines.CustomPipeline"]
settings.pipeline.handle_batch_max_size = 100
settings.pipeline.handle_interval = 5

# 配置 MySQL
settings.mysql.host = "localhost"
settings.mysql.port = 3306
settings.mysql.db = "spider_db"
settings.mysql.user = "root"
settings.mysql.password = "password"
```

## 方式二：配置文件

在项目根目录创建 `settings.py`：

```python
# settings.py
from maize import SpiderSettings


class Settings(SpiderSettings):
    # 基础配置
    project_name = "我的爬虫项目"
    concurrency = 10
    log_level = "INFO"
    downloader = "maize.AioHttpDownloader"

    # 日志处理器
    logger_handler = ""

    # 分布式配置
    is_distributed = False
```

在爬虫中引用：

```python
if __name__ == "__main__":
    # 默认加载 settings.Settings
    MySpider().run(settings_path="settings.Settings")
```

## 方式三：custom_settings（最高优先级）

在 Spider 类中直接配置：

```python
from maize import Spider


class MySpider(Spider):
    custom_settings = {
        "concurrency": 5,
        "log_level": "DEBUG",
        "downloader": "maize.HTTPXDownloader",
        "request": {
            "verify_ssl": False,
            "request_timeout": 30,
            "max_retry_count": 3,
        },
        "pipeline": {
            "pipelines": ["my_project.pipelines.CustomPipeline"],
            "handle_batch_max_size": 50,
        }
    }

    # ...爬虫实现...
```

## 方式四：环境变量和 .env 文件

### 使用 .env 文件

创建 `.env` 文件：

```env
# 基础配置
PROJECT_NAME=我的爬虫
CONCURRENCY=10
LOG_LEVEL=INFO
DOWNLOADER=maize.HTTPXDownloader

# 请求配置（使用点号分隔嵌套配置）
REQUEST.VERIFY_SSL=false
REQUEST.REQUEST_TIMEOUT=30
REQUEST.MAX_RETRY_COUNT=3

# MySQL 配置
MYSQL.HOST=localhost
MYSQL.PORT=3306
MYSQL.DB=spider_db
MYSQL.USER=root
MYSQL.PASSWORD=password

# Redis 配置
REDIS.HOST=localhost
REDIS.PORT=6379
REDIS.PASSWORD=your_password
```

### 使用系统环境变量

```bash
# Windows PowerShell
$env:PROJECT_NAME="我的爬虫"
$env:CONCURRENCY="10"
$env:REQUEST.VERIFY_SSL="false"

# Linux/Mac
export PROJECT_NAME="我的爬虫"
export CONCURRENCY=10
export REQUEST.VERIFY_SSL=false
```

## 方式五：YAML 配置文件

创建 `settings.yaml`：

```yaml
project_name: 我的爬虫项目
concurrency: 10
log_level: INFO
downloader: maize.HTTPXDownloader

request:
  verify_ssl: false
  request_timeout: 30
  max_retry_count: 3
  random_wait_time: [1, 3]

pipeline:
  pipelines:
    - my_project.pipelines.CustomPipeline
  handle_batch_max_size: 100
  handle_interval: 5

mysql:
  host: localhost
  port: 3306
  db: spider_db
  user: root
  password: password

redis:
  host: localhost
  port: 6379
  db: 0
  password: your_password
```

## 方式六：TOML 配置文件

创建 `settings.toml`：

```toml
project_name = "我的爬虫项目"
concurrency = 10
log_level = "INFO"
downloader = "maize.HTTPXDownloader"

[request]
verify_ssl = false
request_timeout = 30
max_retry_count = 3
random_wait_time = [1, 3]

[pipeline]
pipelines = ["my_project.pipelines.CustomPipeline"]
handle_batch_max_size = 100
handle_interval = 5

[mysql]
host = "localhost"
port = 3306
db = "spider_db"
user = "root"
password = "password"

[redis]
host = "localhost"
port = 6379
db = 0
password = "your_password"
```

## 完整配置项

### 基础配置（SpiderSettings）

| 配置项              | 类型     | 默认值                      | 说明             |
|:-----------------|:-------|:-------------------------|:---------------|
| `project_name`   | `str`  | `"project name"`         | 项目名称           |
| `concurrency`    | `int`  | `1`                      | 并发数            |
| `downloader`     | `str`  | `"maize.AioHttpDownloader"` | 下载器类路径         |
| `log_level`      | `str`  | `"INFO"`                 | 日志级别           |
| `logger_handler` | `str`  | `""`                     | 自定义日志处理器类路径    |
| `is_distributed` | `bool` | `False`                  | 是否使用分布式爬虫      |
| `maize_cob_api`  | `str`  | `""`                     | maize-cob API 地址 |

### 请求配置（RequestSettings）

| 配置项                 | 类型              | 默认值       | 说明                             |
|:--------------------|:----------------|:----------|:-------------------------------|
| `verify_ssl`        | `bool`          | `True`    | 是否验证 SSL 证书                    |
| `request_timeout`   | `int`           | `60`      | 请求超时时间（秒）                      |
| `random_wait_time`  | `Tuple[int, int]` | `(0, 0)`  | 随机等待时间范围（秒），如 `(1, 3)` 表示1-3秒 |
| `use_session`       | `bool`          | `True`    | 是否使用 session（HTTPXDownloader 不支持） |
| `max_retry_count`   | `int`           | `0`       | 请求最大重试次数                       |

使用示例：

```python
settings = SpiderSettings()
settings.request.verify_ssl = False
settings.request.request_timeout = 30
settings.request.max_retry_count = 3
settings.request.random_wait_time = (1, 3)  # 每次请求前随机等待1-3秒
```

### 数据管道配置（PipelineSettings）

| 配置项                          | 类型           | 默认值                           | 说明                      |
|:-----------------------------|:-------------|:------------------------------|:------------------------|
| `pipelines`                  | `List[str]`  | `["maize.BasePipeline"]`      | 数据管道列表                  |
| `max_cache_count`            | `int`        | `5000`                        | item 在内存队列中最大缓存数量       |
| `handle_batch_max_size`      | `int`        | `1000`                        | item 每批入库的最大数量          |
| `handle_interval`            | `int`        | `2`                           | item 入库时间间隔（秒）          |
| `error_max_retry_count`      | `int`        | `5`                           | 入库异常的 item 最大重试次数       |
| `error_max_cache_count`      | `int`        | `5000`                        | 入库异常的 item 在内存队列中最大缓存数量 |
| `error_retry_batch_max_size` | `int`        | `1`                           | 入库异常的 item 重试每批处理的最大数量  |
| `error_handle_batch_max_size` | `int`        | `1000`                        | 入库异常的 item 超过重试次数后每批处理的最大数量 |
| `error_handle_interval`      | `int`        | `60`                          | 处理入库异常的 item 时间间隔（秒）   |

使用示例：

```python
settings = SpiderSettings()
settings.pipeline.pipelines = [
    "my_project.pipelines.CustomPipeline",
    "my_project.pipelines.MysqlPipeline"
]
settings.pipeline.handle_batch_max_size = 100
settings.pipeline.handle_interval = 5
```

### RPA 配置（RPASettings）

| 配置项                   | 类型              | 默认值                           | 说明                                            |
|:----------------------|:----------------|:------------------------------|:----------------------------------------------|
| `use_stealth_js`      | `bool`          | `True`                        | 是否使用 stealth js                              |
| `stealth_js_path`     | `Path`          | `"utils/js/stealth.min.js"`   | stealth js 文件路径                               |
| `headless`            | `bool`          | `True`                        | 是否为无头浏览器                                      |
| `driver_type`         | `str`           | `"chromium"`                  | 浏览器驱动类型：chromium/firefox/webkit              |
| `user_agent`          | `Optional[str]` | `None`                        | User Agent                                    |
| `window_size`         | `Tuple[int, int]` | `(1024, 800)`                 | 窗口大小                                          |
| `executable_path`     | `Optional[str]` | `None`                        | 浏览器可执行文件路径                                    |
| `download_path`       | `Optional[str]` | `None`                        | 下载文件的路径                                       |
| `render_time`         | `Optional[int]` | `None`                        | 渲染时长（秒）                                       |
| `wait_until`          | `str`           | `"domcontentloaded"`          | 页面加载等待策略                                      |
| `skip_resource_types` | `List[str]`     | `[]`                          | 不加载的资源类型列表，如 `["image", "media", "font"]`   |
| `skip_url_patterns`   | `List[str]`     | `[]`                          | 跳过的 URL 模式                                    |
| `custom_argument`     | `List[str]`     | `["--no-sandbox", ...]`       | 自定义浏览器渲染参数                                    |
| `endpoint_url`        | `Optional[str]` | `None`                        | CDP websocket 端点                              |
| `slow_mo`             | `Optional[float]` | `None`                        | RPA 操作减慢时间（毫秒）                               |
| `url_regexes`         | `List[str]`     | `[]`                          | 拦截 xhr 接口正则表达式列表                             |
| `url_regexes_save_all` | `bool`          | `False`                       | 是否保存所有拦截的接口                                   |

使用示例：

```python
settings = SpiderSettings(
    downloader="maize.downloader.playwright_downloader.PlaywrightDownloader"
)
settings.rpa.headless = False  # 显示浏览器窗口
settings.rpa.driver_type = "chromium"
settings.rpa.window_size = (1920, 1080)
settings.rpa.skip_resource_types = ["image", "media", "font"]  # 不加载图片、媒体、字体
settings.rpa.wait_until = "networkidle"  # 等待网络空闲
```

### Redis 配置（RedisSettings）

| 配置项             | 类型              | 默认值           | 说明               |
|:----------------|:----------------|:--------------|:-----------------|
| `use_redis`     | `bool`          | `False`       | 是否使用 Redis      |
| `host`          | `str`           | `"localhost"` | Redis 主机         |
| `port`          | `int`           | `6379`        | Redis 端口         |
| `db`            | `int`           | `0`           | Redis 数据库        |
| `username`      | `Optional[str]` | `None`        | Redis 用户名        |
| `password`      | `Optional[str]` | `None`        | Redis 密码         |
| `key_prefix`    | `str`           | `"maize"`     | Redis key 前缀     |
| `key_lock`      | `str`           | `"lock"`      | Redis lock key   |
| `key_running`   | `str`           | `"running"`   | Redis running key |
| `key_queue`     | `str`           | `"queue"`     | Redis queue key  |

使用示例：

```python
settings = SpiderSettings()
settings.redis.use_redis = True
settings.redis.host = "192.168.1.100"
settings.redis.port = 6379
settings.redis.password = "your_password"
settings.redis.db = 0

# 获取 Redis URL
redis_url = settings.redis.url  # redis://192.168.1.100:6379/0
```

### 代理配置（ProxySettings）

| 配置项              | 类型     | 默认值     | 说明                 |
|:-----------------|:-------|:--------|:-------------------|
| `enabled`        | `bool` | `False` | 是否启用代理             |
| `proxy_url`      | `str`  | `""`    | 代理地址（不包含协议）        |
| `proxy_username` | `str`  | `""`    | 代理用户名              |
| `proxy_password` | `str`  | `""`    | 代理密码               |

使用示例：

```python
settings = SpiderSettings()
settings.proxy.enabled = True
settings.proxy.proxy_url = "proxy.example.com:8080"
settings.proxy.proxy_username = "user"
settings.proxy.proxy_password = "password"

# 获取代理字典
proxy_dict = settings.proxy.proxy_dict
# {'http': 'http://user:password@proxy.example.com:8080',
#  'https': 'http://user:password@proxy.example.com:8080'}
```

### MySQL 配置（MySQLSettings）

| 配置项        | 类型          | 默认值           | 说明         |
|:-----------|:------------|:--------------|:-----------|
| `host`     | `str`       | `"localhost"` | MySQL 主机   |
| `port`     | `str | int` | `3306`        | MySQL 端口   |
| `db`       | `str`       | `""`          | MySQL 数据库名 |
| `user`     | `str`       | `""`          | MySQL 用户名  |
| `password` | `str`       | `""`          | MySQL 密码   |

使用示例：

```python
settings = SpiderSettings()
settings.mysql.host = "localhost"
settings.mysql.port = 3306
settings.mysql.db = "spider_db"
settings.mysql.user = "root"
settings.mysql.password = "password"
```

## 最佳实践

### 1. 开发与生产环境分离

```python
# settings.py
import os
from maize import SpiderSettings


class Settings(SpiderSettings):
    # 从环境变量读取配置
    project_name = os.getenv("PROJECT_NAME", "我的爬虫")
    concurrency = int(os.getenv("CONCURRENCY", "10"))
    log_level = os.getenv("LOG_LEVEL", "INFO")


# 开发环境：.env.dev
PROJECT_NAME=开发爬虫
CONCURRENCY=2
LOG_LEVEL=DEBUG

# 生产环境：.env.prod
PROJECT_NAME=生产爬虫
CONCURRENCY=20
LOG_LEVEL=INFO
```

### 2. 敏感信息使用环境变量

```python
# 不要在代码中硬编码密码
settings = SpiderSettings()
settings.mysql.password = os.getenv("MYSQL_PASSWORD")
settings.redis.password = os.getenv("REDIS_PASSWORD")
```

### 3. 配置验证

```python
from maize import SpiderSettings


def validate_settings(settings: SpiderSettings):
    """验证配置"""
    if settings.concurrency > 100:
        raise ValueError("并发数不能超过100")

    if settings.mysql.db and not settings.mysql.password:
        raise ValueError("MySQL 配置缺少密码")

    return settings


settings = validate_settings(SpiderSettings())
```

### 4. 多爬虫共享配置

```python
# base_settings.py
from maize import SpiderSettings


class BaseSettings(SpiderSettings):
    """基础配置，所有爬虫共享"""
    log_level = "INFO"
    concurrency = 10


# spider1_settings.py
from base_settings import BaseSettings


class Spider1Settings(BaseSettings):
    """Spider1 专属配置"""
    project_name = "爬虫1"
    concurrency = 5  # 覆盖基础配置
```

## 下一步

- [Request 详解](request.md) - 请求参数说明
- [Pipeline 管道](pipeline.md) - 数据管道配置
- [下载器](downloader.md) - 下载器配置与自定义
