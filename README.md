# codex-delegate (delegation skill)

一个 agent 技能（skill）：把有边界的开发任务委派给本地安装的 OpenAI Codex CLI——模型发现与选择、推理力度（reasoning effort）控制、会话延续（同一会话内多轮迭代）、缓存感知的重复评审/写作。适合"让另一个模型干一段活、拿回结果继续主线"的工作流。

## 功能

- **模型发现**：枚举本机 Codex CLI 可用模型，按任务特征选型（`references/model-control.md`）
- **委派执行**：`scripts/run.py` 包装 CLI 调用，统一参数与输出解析
- **会话延续**：跨多轮保持上下文，支持追问与迭代（`references/session-cache.md`）
- **健康自检**：`--doctor` 检查 CLI 安装/版本/登录态（`references/maintenance.md`）

## 安装

```bash
git clone https://github.com/techdou/codex-delegate.git ~/.agents/skills/codex-delegate
```

前置：本机已安装并登录 OpenAI Codex CLI。

## 用法

由 agent 按 `SKILL.md` 自动调度；手动体检：

```bash
python3 scripts/run.py --doctor
```

## 目录

```
SKILL.md              技能入口（agent 读这里）
references/           分域参考：模型控制/会话缓存/安全/维护/官方 CLI 对应关系
scripts/              run.py（入口）+ model_catalog.py + session_state.py
evals/                质量评估用例
```

## License

[MIT](LICENSE)
