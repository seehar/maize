from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    YamlConfigSettingsSource,
)

from maize.common.constant.setting_constant import (
    LogLevelEnum,
    PipelineEnum,
    RPADriverTypeEnum,
    RPAWaitUntilEnum,
    SpiderDownloaderEnum,
)

BASE_DIR = Path(__file__).parent.parent


class RequestSettings(BaseModel):
    """请求配置"""

    verify_ssl: bool = Field(default=True, description="是否验证 SSL 证书")
    request_timeout: int = Field(default=60, description="请求超时时间，单位：秒")
    random_wait_time: tuple[int, int] = Field(default=(0, 0), description="随机等待时间，单位：秒")
    use_session: bool = Field(default=True, description="是否使用 session（HTTPXDownloader 不支持）")
    max_retry_count: int = Field(default=0, description="请求最大重试次数")


class PipelineSettings(BaseModel):
    """数据管道配置"""

    # 数据管道，支持多个数据管道
    pipelines: list[str] = Field(default=[PipelineEnum.EMPTY.value], description="数据管道列表")

    # Item 正常处理配置
    max_cache_count: int = Field(default=5000, description="item在内存队列中最大缓存数量")
    handle_batch_max_size: int = Field(default=1000, description="item每批入库的最大数量")
    handle_interval: int = Field(default=2, description="item入库时间间隔，单位：秒")

    # 异常 Item 处理配置
    error_max_retry_count: int = Field(default=5, description="入库异常的 item 最大重试次数")
    error_max_cache_count: int = Field(default=5000, description="入库异常的 item 在内存队列中最大缓存数量")
    error_retry_batch_max_size: int = Field(default=1, description="入库异常的 item 重试每批处理的最大数量")
    error_handle_batch_max_size: int = Field(
        default=1000, description="入库异常的 item 超过重试次数后，每批处理的最大数量"
    )
    error_handle_interval: int = Field(default=60, description="处理入库异常的 item 时间间隔，单位：秒")


class RPASettings(BaseModel):
    """RPA 浏览器配置"""

    # 使用 stealth js
    use_stealth_js: bool = Field(default=True, description="是否使用 stealth js")
    # stealth js 文件路径
    stealth_js_path: Path = Field(default=BASE_DIR / "utils/js/stealth.min.js", description="stealth js 文件路径")
    # 是否为无头浏览器
    headless: bool = Field(default=True, description="是否为无头浏览器")
    # 浏览器驱动类型
    driver_type: str = Field(default=RPADriverTypeEnum.CHROMIUM.value, description="浏览器驱动类型")
    # 请求头
    user_agent: str | None = Field(default=None, description="User Agent")
    # 窗口大小
    window_size: tuple[int, int] = Field(default=(1024, 800), description="窗口大小")
    # 浏览器路径
    executable_path: str | None = Field(default=None, description="浏览器可执行文件路径")
    # 下载文件的路径
    download_path: str | None = Field(default=None, description="下载文件的路径")
    # 渲染时长
    render_time: int | None = Field(default=None, description="渲染时长，单位：秒")
    # 页面加载等待策略
    wait_until: str = Field(
        default=RPAWaitUntilEnum.DOMCONTENTLOADED.value,
        description="页面加载等待策略: 'commit'(仅导航完成), 'domcontentloaded'(DOM加载完成), 'load'(等待所有资源), 'networkidle'(网络空闲)",
    )
    # 不加载资源类型列表
    skip_resource_types: list[str] = Field(default=[], description="不加载的资源类型列表")
    # 跳过的 URL 模式
    skip_url_patterns: list[str] = Field(default=[], description="跳过的 URL 模式")
    # 自定义浏览器渲染参数
    custom_argument: list[str] = Field(
        default=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        description="自定义浏览器渲染参数",
    )
    # CDP websocket 端点
    endpoint_url: str | None = Field(default=None, description="CDP websocket 端点")
    # 操作减慢时间
    slow_mo: float | None = Field(default=None, description="RPA 操作减慢时间，单位：毫秒")
    # 拦截 xhr 接口正则表达式列表
    url_regexes: list[str] = Field(default=[], description="拦截 xhr 接口正则表达式列表")
    # 是否保存所有拦截的接口
    url_regexes_save_all: bool = Field(default=False, description="是否保存所有拦截的接口")


class RedisSettings(BaseModel):
    """Redis 配置"""

    use_redis: bool = Field(default=False, description="是否使用 Redis")
    host: str = Field(default="localhost", description="Redis 主机")
    port: int = Field(default=6379, description="Redis 端口")
    db: int = Field(default=0, description="Redis 数据库")
    username: str | None = Field(default=None, description="Redis 用户名")
    password: str | None = Field(default=None, description="Redis 密码")
    key_prefix: str = Field(default="maize", description="Redis key 前缀")
    key_lock: str = Field(default="lock", description="Redis lock key")
    key_running: str = Field(default="running", description="Redis running key")
    key_queue: str = Field(default="queue", description="Redis queue key")

    @property
    def url(self) -> str:
        """生成 Redis 连接 URL"""
        url_username_password = ""
        if self.username or self.password:
            url_username_password = f"{self.username or ''}:{self.password or ''}@"
        return f"redis://{url_username_password}{self.host}:{self.port}/{self.db}"


class ProxySettings(BaseModel):
    """代理配置"""

    # 代理，示例：xxx.xxx:2132（不包含 http:// 或 https://）
    proxy_url: str = Field(default="", description="代理地址")
    proxy_username: str = Field(default="", description="代理用户名")
    proxy_password: str = Field(default="", description="代理密码")

    # 建议添加:
    enabled: bool = Field(default=False, description="是否启用代理")

    @property
    def proxy_dict(self) -> dict | None:
        """生成代理字典"""
        if not self.enabled or not self.proxy_url:
            return None

        if self.proxy_username and self.proxy_password:
            return {
                "http": f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_url}",
                "https": f"http://{self.proxy_username}:{self.proxy_password}@{self.proxy_url}",
            }
        return {"http": f"http://{self.proxy_url}", "https": f"http://{self.proxy_url}"}


class MySQLSettings(BaseModel):
    """MySQL 数据库配置"""

    host: str = Field(default="localhost", description="MySQL 主机")
    port: str | int = Field(default=3306, description="MySQL 端口")
    db: str = Field(default="", description="MySQL 数据库名")
    user: str = Field(default="", description="MySQL 用户名")
    password: str = Field(default="", description="MySQL 密码")


class MiddlewareSettings(BaseModel):
    """中间件配置"""

    model_config = {"arbitrary_types_allowed": True}

    downloader_middlewares: dict[str | type, int] = Field(
        default_factory=dict,
        description="下载器中间件配置，格式: {'middleware.path': priority} 或 {MiddlewareClass: priority}",
    )

    spider_middlewares: dict[str | type, int] = Field(
        default_factory=dict,
        description="爬虫中间件配置，格式: {'middleware.path': priority} 或 {MiddlewareClass: priority}",
    )

    pipeline_middlewares: dict[str | type, int] = Field(
        default_factory=dict,
        description="管道中间件配置，格式: {'middleware.path': priority} 或 {MiddlewareClass: priority}",
    )

    enable_builtin_middlewares: bool = Field(
        default=True,
        description="是否启用内置中间件",
    )


class SpiderSettings(BaseSettings):
    """爬虫配置主类"""

    # 基础配置
    project_name: str = Field(default="project name", description="项目名称")
    concurrency: int = Field(default=1, description="并发数")

    # 下载器配置
    downloader: str = Field(default=SpiderDownloaderEnum.AIOHTTP.value, description="下载器")

    # 日志配置
    log_level: str = Field(default=LogLevelEnum.INFO.value, description="日志级别")
    logger_handler: str = Field(default="", description="日志 handler")

    # 是否使用分布式爬虫
    is_distributed: bool = Field(default=False, description="是否使用分布式爬虫")

    # maize-cob 配置
    maize_cob_api: str = Field(default="", description="maize-cob API 地址")

    # 子配置
    request: RequestSettings = Field(default_factory=RequestSettings, description="请求配置")
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings, description="数据管道配置")
    rpa: RPASettings = Field(default_factory=RPASettings, description="RPA 配置")
    redis: RedisSettings = Field(default_factory=RedisSettings, description="Redis 配置")
    proxy: ProxySettings = Field(default_factory=ProxySettings, description="代理配置")
    mysql: MySQLSettings = Field(default_factory=MySQLSettings, description="MySQL 配置")
    middleware: MiddlewareSettings = Field(default_factory=MiddlewareSettings, description="中间件配置")

    # 支持 .env, yml, toml 等格式
    model_config = SettingsConfigDict(
        env_file=".env",
        yaml_file="settings.yaml",
        toml_file="settings.toml",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter=".",
        nested_model_default_partial_update=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type["BaseSettings"],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        加载优先级：
        1️. 初始化参数
        2️. 系统环境变量
        3️. .env 文件
        4️. YAML 文件
        5️. TOML 文件
        6️. 文件机密目录（如 /var/run/secrets）
        """
        yaml_source = YamlConfigSettingsSource(settings_cls, yaml_file_encoding="utf-8")
        toml_source = TomlConfigSettingsSource(settings_cls)

        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_source,
            toml_source,
            file_secret_settings,
        )

    def merge_settings(self, settings: "SpiderSettings") -> "SpiderSettings":
        """
        合并另一个 Settings 实例的配置到当前实例

        :param settings: 要合并的 Settings 实例
        :return: 当前实例
        """
        # 获取所有字段名
        field_names: list[str] = list(self.__class__.model_fields.keys())
        for field_name in field_names:
            new_value = getattr(settings, field_name)
            current_value = getattr(self, field_name)

            # 只更新与当前值不同的字段，保留原始对象类型
            if new_value != current_value:
                setattr(self, field_name, new_value)

        return self

    def merge_settings_from_dict(self, settings_dict: dict[str, Any]) -> "SpiderSettings":
        """
        合并 dict 的配置到当前实例

        :param settings_dict: dict 类型的配置
        :return: 当前实例
        """
        # 创建更新后的实例
        updated_self = self.model_copy(update=settings_dict, deep=True)

        # 使用 __dict__.update() 直接更新当前实例的字段，保持模型实例类型
        self.__dict__.update(updated_self.__dict__)

        return self

    @property
    def redis_url(self) -> str:
        """生成 Redis 连接 URL（向后兼容）"""
        return self.redis.url
