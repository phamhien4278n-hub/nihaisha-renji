# Hindsight 故障排查与队列清理

## 快速诊断

```bash
# 看日志有无 retry_blocked
ssh ubuntu@XX.XX.XX.XX "sudo journalctl -u hindsight --no-pager -n 20 --no-hostname | grep retry_blocked"

# 看日志中 recall 详情（candidates 数量、rerank 耗时）
ssh ubuntu@XX.XX.XX.XX "sudo journalctl -u hindsight --no-pager --since '5 min ago' --no-hostname | grep RECALL"
```

## 常见故障模式

| 症状 | 原因 | 修复 |
|------|------|------|
| recall 返回 401 | rerank provider 的 API key 无效 | 检查 `.env` 中 RERANKER 相关配置 |
| recall 返回 "No relevant memories" 但 DB 有数据 | 索引队列卡死（retry_blocked=1） | 清理 async_operations 并重启 |
| retain 正常但 recall 无结果 | consolidation 任务未完成或 bm25 索引未更新 | 等 consolidation 跑完，或重新 retain 触发索引 |
| 错误日志显示 "Unknown reranker provider" | provider 名拼错 | 检查支持的 provider 列表 |

## 核心问题：Consolidation 队列卡死

### 识别

日志出现 `retry_blocked=1`：
```
[PENDING_BREAKDOWN] consolidation: total=1 claimable=0 payload_null=0 retry_blocked=1 assigned=0
```

**原因**：旧任务因 DeepSeek API 401 失败，被标记为不可重试，永远卡在队列中。

### 修复步骤

```bash
# 1. SSH 登录
ssh ubuntu@XX.XX.XX.XX

# 2. 用 Hindsight 自带的 venv python 清理卡死任务
/home/ubuntu/hindsight/venv/bin/python3 -c "
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='hindsight', user='hindsight', password='XXXX')
cur = conn.cursor()
cur.execute('SELECT count(*) FROM async_operations')
print('Before:', cur.fetchone()[0])
cur.execute('DELETE FROM async_operations')
print('Deleted:', cur.rowcount)
conn.commit()
conn.close()
"

# 3. 重启服务
sudo systemctl restart hindsight

# 4. 等 50 秒模型加载，然后用 hindsight_retain 重新存入知识触发新索引
```

## 数据库速查

Hindsight 使用 PostgreSQL，连接信息在 `.env` 中 `HINDSIGHT_API_DATABASE_URL`。

### 关键表

| 表 | 说明 |
|----|------|
| `memory_units` | 记忆本体（content + embedding） |
| `async_operations` | 异步任务队列（consolidation, retain, batch_retain） |
| `entities` | 提取的实体 |
| `chunks` | 文本分块 |

### 快速查询

```bash
/home/ubuntu/hindsight/venv/bin/python3 -c "
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='hindsight', user='hindsight', password='XXXX')
cur = conn.cursor()

# 总记忆数
cur.execute('SELECT count(*) FROM memory_units')
print('Memories:', cur.fetchone()[0])

# 队列状态
cur.execute('SELECT operation_type, status, retry_count FROM async_operations')
for r in cur.fetchall():
    print('Queue:', r)

# 最新记忆（按 context 字段）
cur.execute('SELECT substring(context,1,60), created_at FROM memory_units ORDER BY created_at DESC LIMIT 5')
for r in cur.fetchall():
    print(r)

conn.close()
"
```

## 索引恢复验证

清理队列后，用 `hindsight_recall` 搜索。观察召回量变化：
- 1条 → 队列刚清，旧索引还在
- 5~9条 → 索引恢复中
- 应该能搜到新存内容 → 完全恢复

如果新存内容搜不到但旧内容可以，说明新内容的索引还没跑完，等待 consolidation 完成即可。
