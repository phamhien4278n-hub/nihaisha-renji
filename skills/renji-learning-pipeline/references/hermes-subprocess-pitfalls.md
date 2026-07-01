# Supervisor 调试踩坑记录

## 2026-06-30: hermes 子进程崩溃循环

### 现象

supervisor 启动后每 2 秒生成一个 61 字节的日志文件，hermes 子进程瞬间退出。

### 根因

**Python `subprocess.Popen` 不继承 MSYS 的盘符挂载（`/g`, `/c` 等）。**

错误做法（日志显示 `cd: /g/hermes: No such file or directory`）：

```python
cmd = ["bash", "-l", "-c", "cd /g/hermes && hermes -z '...' --yolo"]
proc = subprocess.Popen(cmd, ...)
```

即使 `bash -l` 在终端里能找到 `/g/hermes`，从 Python subprocess 调用的 bash 也找不到——因为 MSYS 的盘符挂载是由 MSYS DLL 在交互式终端里建立的，非交互式 `bash -l` 的 Popen 不会触发挂载。

正确做法（直接调 hermes.exe + Popen cwd 参数）：

```python
cmd = ["G:/hermes/venv/Scripts/hermes.exe", "-z", instruction, "--yolo"]
proc = subprocess.Popen(cmd, cwd="G:/hermes", ...)
```

### 第二条弯路：hermes 是 bash 函数不是二进制

`hermes` 在 `~/.bashrc` 中定义为 bash 函数，不是系统 PATH 上的可执行文件。所以即使 `bash -l -c "hermes"` 在终端里能用，Popen 直接调 `bash -l -c "hermes"` 也可能找不到（因为函数加载依赖于交互式环境）。

**实际入口**：`G:/hermes/venv/Scripts/hermes.exe`

### 验证方法

用 Python 脚本直接测试 Popen 调用：

```python
import subprocess
r = subprocess.run(
    ['G:/hermes/venv/Scripts/hermes.exe', '-z', 'test prompt', '--yolo'],
    capture_output=True, text=True, timeout=30,
    cwd='G:/hermes'
)
print(r.returncode, r.stdout[:200])
```
