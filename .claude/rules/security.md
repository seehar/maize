# 安全规则

## 敏感信息

1. **禁止硬编码密钥和凭证**
   - API keys, tokens, passwords 必须使用环境变量
   - 配置信息优先放在 `maize/settings/` 或 `.env` 文件

2. **禁止提交敏感文件**
   - `.env`, `*.pem`, `*.key`, `credentials.json` 等禁止提交
   - 确保 `.gitignore` 正确配置

## 网络安全

1. **请求安全**
   - 爬虫请求需设置合理的 User-Agent 和请求间隔
   - 遵守目标网站的 `robots.txt`

2. **代理使用**
   - 使用代理时确保代理来源可靠
   - 敏感操作不使用免费代理
