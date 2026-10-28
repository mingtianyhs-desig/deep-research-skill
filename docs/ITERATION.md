# 迭代开发指南 · Iteration Guide

本仓库是你自己的 fork，用于**使用 + 持续迭代优化**。本文档记录本地工作流、环境约定和已知事项。

---

## 1. Git 远程拓扑

```
origin    https://github.com/mingtianyhs-desig/deep-research-skill.git   ← 你的 fork（可写）
upstream  https://github.com/lovstudio/deep-research-skill.git           ← 原作者（只读）
```

- `push` 默认走 `origin`
- `main` 跟踪 `origin/main`

### 查看当前状态

```bash
git remote -v
git status -sb
```

### 同步上游更新

```bash
git fetch upstream
git merge upstream/main        # 保留本地提交历史，推荐
# 或
git rebase upstream/main       # 保持线性历史，本地未推送时可选用
```

若 `main` 上已有你的迭代提交，`merge` 更安全；冲突集中在被改动的文件上。

### 日常迭代流程

```bash
git switch -c feat/your-change      # 每个改动开一个分支
# ... 编辑、测试 ...
git add -A && git commit -m "feat: 说明改了什么"
git push -u origin feat/your-change
```

改动验证通过后再合回 `main`：

```bash
git switch main
git merge --no-ff feat/your-change
git push origin main
```

---

## 2. 目录职责

| 路径 | 作用 | 迭代注意 |
|------|------|----------|
| `SKILL.md` | 技能入口，渐进式披露 | 保持精简；细节下沉到 `reference/` |
| `skill.yaml` | 清单：id / version / profile 契约 | 改版本号要同步 `SKILL.md` metadata 和 `README.md` |
| `reference/*.md` | 各阶段方法论（8 阶段流水线、质检、富媒体等） | 改流程先改这里，再改 `SKILL.md` 的指向 |
| `references/skill-composition.md` | 与邻近技能的协作/移交 | 改依赖时同步 `SKILL.md` 的 `depends_on` |
| `scripts/*.py` | 可执行校验与编排（纯标准库） | 改动必须配测试 |
| `schemas/*.json` | 证据/来源/主张/运行清单的结构 | 改 schema 要同步 `scripts/` 里的读写逻辑 |
| `templates/` | Markdown 报告模板 + McKinsey HTML 模板 | 改结构要同步 `scripts/validate_report.py` |
| `tests/` | unittest 用例 | 新增校验规则必带正反用例 |

---

## 3. 运行与测试（Windows）

本机环境：Python 3.14.7，pytest 9.1.1，无额外 pip 依赖（脚本仅用标准库）。

```powershell
# 全量测试（注意 < NUL，见下方说明）
cmd /c "python -m pytest tests -q < NUL 2>&1"

# 单个模块
cmd /c "python -m pytest tests\test_validate_report.py -q < NUL 2>&1"
```

**当前基线：58 passed。**

### 为什么需要 `< NUL`

测试内部用 `subprocess.run(..., capture_output=True)` 调用脚本。在部分受限/无控制台的宿主环境里，Python 继承的 stdin 句柄无效，会抛：

```
OSError: [WinError 6] 句柄无效
```

重定向 stdin 后即可正常执行。**这是宿主环境限制，不是仓库缺陷**；在普通终端里直接 `python -m pytest tests -q` 通常正常。

### 脚本冒烟

```powershell
python scripts\validate_report.py -r <报告路径>
python scripts\verify_citations.py -r <报告路径>
python scripts\source_evaluator.py --url <URL> --title "<标题>"
python scripts\citation_manager.py --help
```

退出码：`0` 通过，非 `0` 失败 —— 可直接用于 CI 门禁。

---

## 4. 已知事项 / 可选依赖

| 项 | 状态 | 说明 |
|----|------|------|
| `weasyprint` | 未安装 | 仅 PDF 输出需要：`pip install weasyprint`。缺失时 HTML/Markdown 输出不受影响 |
| `search-cli` | 未安装 | 多源搜索聚合（Brave/Serper/Exa/Jina/Firecrawl），`brew` 方案在 Windows 不可用；技能已声明可回退到内置 web search |
| `tests/fixtures/valid_report.md` | **已过期** | v2.6.0 引入图表硬性要求后，该 fixture 不再能通过 `validate_report.py`（缺 figures）。且目前**没有任何测试引用**这两个 fixture。可作为首个清理项 |
| `tests/fixtures/invalid_report.md` | 语义过期 | 同上，未被测试引用 |

> 注：以上 fixture 问题不影响 58 个测试通过，属于文档/样例债。

---

## 5. 迭代方向（建议起点）

按「先止血、再结构」的顺序：

1. **样例债清理** — 让 `tests/fixtures/*.md` 重新可用，或改为由测试动态生成；补一条 fixture 级回归测试。
2. **跨平台适配** — `requirements.txt` 与 README 的安装说明偏 macOS（`brew`）。可补 Windows/PowerShell 等价方案。
3. **校验规则可配置** — `validate_report.py` 的阈值（源数量、字数、图表下限）目前硬编码在脚本里，可抽到配置/模式表，便于按 Quick/Standard/Deep/UltraDeep 调整。
4. **CI** — 加 GitHub Actions：`pytest` + 对 fixtures 跑校验，防止迭代回归。
5. **版本一致性** — `SKILL.md`(metadata.version)、`skill.yaml`(version)、`README.md`(badge) 三处需同步，可写脚本校验。

---

## 6. 提交约定

沿用上游风格（Conventional Commits + 版本号）：

```
feat(deep-research): 新增能力 (v2.7.0)
fix(deep-research): 修复缺陷 (v2.6.2)
chore: 杂项
docs: 文档
test: 测试
```

改动涉及行为时，同步更新：
- `CHANGELOG.md`
- `SKILL.md` 的 `metadata.version`
- `skill.yaml` 的 `version`
- `README.md` 的 badge 与 Version History 表
