# Hermes 子进程调用陷阱

## ❌ 错误方式：管道输入

```bash
echo "instruction" | hermes -z --yolo
```

结果：`hermes: error: argument -z/--oneshot: expected one argument`

原因：`-z` 模式下 hermes 不接受 stdin 管道，必须用 `-z "prompt"` 直接传参。

## ✅ 正确方式：-z 直接传参

```bash
hermes -z "完整的任务指令" --yolo
```

`-z` 接受一个字符串作为一次性 prompt，执行完退出。`--yolo` 自动批准所有危险操作（无用户交互的子进程必需）。

## ⚠️ 中文 prompt 与 shell 转义

中文字符在 bash 双引号中通常安全，但尽量避免在 prompt 中包含：
- 反引号 `` ` ``
- `$` 符号
- 未转义的双引号

如果 prompt 中包含这些字符，需用转义或单引号。

## ⚠️ 上下文隔离

`hermes -z` 每次启动是新会话，不继承父会话的上下文。需要在 prompt 中明确：
1. 加载哪个 skill
2. 读哪个文件
3. 当前任务是什么
4. 完成后退出（不要闲聊）

## ⚠️ 输出捕获

子进程 stdout 包含完整的 hermes 交互输出（工具调用、思考、最终回复）。学习流水线的日志文件可能很大（单段 50-200KB）。supervisor 脚本的 `stdout=subprocess.PIPE` 会把全部输出读到内存——超时或 OOM 都可能导致失败。

**建议**：直接重定向到文件而非通过 Python PIPE：
```python
with open(log_file, 'w') as f:
    proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
```
