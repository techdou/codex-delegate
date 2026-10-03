# Changelog

## 1.4.3 - 2026-10-04

- rename: codex → codex-delegate（仓库与技能名，避免与 OpenAI Codex CLI 官方产品名混淆；旧链接 GitHub 自动重定向）
## 1.4.2 - 2026-10-02

- 按官方 Agent Skills 规范（agentskills.io specification）完善 frontmatter：新增 `license: MIT`、`compatibility`（Codex CLI + Python 3.10+ 环境要求）、`metadata.version`；description 重写为更清晰的 what/when/when-not 结构并扩充匹配关键词
- SKILL.md 正文面向 Agent 调用重构：新增 **Quick reference** 节置顶（最小调用模板 + 模式速查 + 高频开关），模式选择与 `--no-mcp` 提前；原 session/cache/model/network 各节保留并后移
- 补平台说明：无 `python3` 别名的主机（Windows 常见）用 `python` 调用同一脚本
- Measured pitfalls 补 v1.4.1 行为：Windows 下 wrapper 被外层超时强杀时 OS 级联回收整棵 codex/MCP 进程树，不再泄漏孤儿进程
- `.gitignore` 排除 `*.bak*` 备份文件

## 1.4.1 - 2026-10-02

- Windows：委派子进程树绑定 kill-on-close Job Object，外层强杀 wrapper（宿主 Bash 超时等）时由操作系统级联回收整棵 codex/MCP 进程树——修复 2026-10-02 事故（6 个僵尸 codex 会话 + 35 个 npx MCP 外壳泄漏约 4.4 GB 内存）
- 主执行路径 `subprocess.run` 改为 `Popen + communicate`，超时路径主动关闭 Job 句柄触发全树回收；非 Windows 平台行为不变

## 1.4.0 - 2026-09-10

- 首个公开发布：Codex CLI 委派（模型发现/选择、reasoning 控制、会话延续、缓存感知评审）
- `--doctor` 健康自检
