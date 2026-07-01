# Hindsight Reranker 配置指南

## 问题背景

Hindsight 的搜索流程：查询 → bge-large-zh embedding 召回 → **LLM rerank 重排序** → 返回结果。

如果 rerank API 不可用，`hindsight_recall` 返回 401/500 或 "No relevant memories found"。

## DeepSeek 不提供 rerank

DeepSeek 没有 `/v1/rerank` 端点（返回 404）。不能将 `reranker_provider` 设为 deepseek。

## 国内可用 rerank 提供商

| Provider | API 端点 | 模型 | 价格 |
|----------|---------|------|------|
| **SiliconFlow** 硅基流动 | `https://api.siliconflow.cn/v1/rerank` | BAAI/bge-reranker-v2-m3 | 新用户送 14 元 |
| 阿里云 DashScope | `https://dashscope.aliyuncs.com/.../rerank` | gte-rerank / qwen3-rerank | 按量付费 |

推荐 SiliconFlow：API 格式兼容 OpenAI，Hindsight 原生支持。

## Hindsight 支持的 reranker provider

来自源代码报错信息（`ValueError: Unknown reranker provider`）：
```
local, tei, cohere, zeroentropy, siliconflow, alibaba, google, flashrank, litellm, litellm-sdk, rrf, jina-mlx
```

## 配置方法

### ⚠️ 环境变量优先于 config.json

Hindsight 通过 `.env` 文件（由 systemd `EnvironmentFile` 加载）读取配置，**覆盖 config.json**。

正确配置位置：`/home/ubuntu/hindsight/hindsight.env`

### SiliconFlow 配置

```bash
# /home/ubuntu/hindsight/hindsight.env

# LLM 继续用 DeepSeek（chat API 正常）
HINDSIGHT_API_LLM_PROVIDER=deepseek
HINDSIGHT_API_LLM_API_KEY=sk-xxx
HINDSIGHT_API_LLM_MODEL=deepseek-v4-flash
HINDSIGHT_API_LLM_BASE_URL=https://api.deepseek.com/v1

# Reranker 用 SiliconFlow
HINDSIGHT_API_RERANKER_PROVIDER=siliconflow
HINDSIGHT_API_RERANKER_SILICONFLOW_MODEL=BAAI/bge-reranker-v2-m3
HINDSIGHT_API_RERANKER_SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
HINDSIGHT_API_RERANKER_SILICONFLOW_API_KEY=***
```

### 阿里云 DashScope 配置

```bash
HINDSIGHT_API_RERANKER_PROVIDER=alibaba
```

## API Key 传输陷阱

通过 SSH/heredoc 传递 API key 时，Hermes 安全机制会**自动截断/屏蔽**敏感字符串，导致写入不完整。

**解决方案**：让用户在服务器终端用 `nano` 手动编辑 `.env` 文件，直接敲入完整 key。不再通过 Hermes 中转。

## 验证方法

```bash
# 1. 检查端口
python3 -c "import socket; s=socket.create_connection(('XX.XX.XX.XX',8888),timeout=5); s.close(); print('OK')"

# 2. 服务器上直接测试 SiliconFlow API
curl -s -X POST "https://api.siliconflow.cn/v1/rerank" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-reranker-v2-m3","query":"test","documents":["a","b"]}'

# 3. 用 hindsight_recall 测试
# 不再报 401 = 成功
```
