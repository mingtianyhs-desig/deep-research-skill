# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.7.0] - 2026-10-28

### Changed

- **BREAKING**: 研究报告产出位置从 `~/Documents/[Topic]_Research_[YYYYMMDD]/` 改为相对当前工作目录的 `./research/[主题]_研究_[YYYYMMDD]/`。切换工作区时产出自动跟随，不再写入用户主目录或技能安装目录。
- 目录名改用中文：主题段保留原文语言（英文主题保持英文，中文主题保持中文），其余部分为中文，日期固定 `YYYYMMDD`。
- 移除 `~/.claude/research_output/` 内部 tracking 副本。续写状态文件 `continuation_state_*.json` 改为跟随报告所在目录，避免同一产物出现两个权威副本。
- `research_engine.py` 的输出目录由 `Path.home()/".claude"/"research_output"` 改为 `Path.cwd()/"research"`，并新增 `--out-dir` 参数可覆盖默认值。

### Added

- `reference/report-assembly.md` 新增 `## Path Convention` 一节，明确相对路径约定、中文命名规则、路径非法字符处理与同名目录的 `_2` 后缀策略。
- `SKILL.md` 输出契约新增 Path rule，说明所有路径相对当前工作目录且不额外镜像副本。
- `.gitignore` 新增 `research/`，避免研究产出被误提交。

## [2.6.1] - 2026-10-01

### Changed

- 精简 frontmatter `description` 至 200 字符内，保留原触发语义；完整触发与不触发条件移入正文新增的 `## Triggers`（合并原 “When to Use / NOT Use”）。
- `metadata.tags` 改为列表；`lov-dev-blog` 从 `metadata.dependencies` 移到顶层 `depends_on`，与 `lov-branding-consistency` 并列。
- `skill.yaml` 接入共享 `user-profile/v1` Profile 契约（`read`、`persist` 指向 `skills.deep-research`），原有字段、必填项与提问保持不变，`identity.*` 通过别名桥接 `brand.*`。

### Added

- `references/skill-composition.md`：相邻 Skill、交接边界、重叠决策与组合结论。

## [2.6.0] - 2026-10-01

### Added

- 富媒体成为报告契约：standard 及以上模式必须包含图表（quick ≥1、standard ≥3、deep ≥5、ultradeep ≥8），优先第一手照片、依据引用数字绘制的数据图、结构/流程/时间线示意图与地图。
- 新增 `reference/rich-media.md`：图像来源优先级、照片隐私与 EXIF 处理、版权边界、图注与文件约定、渲染与体积预算。
- `md_to_html.py` 支持图片与图注转换为 `<figure>`，新增 `--embed-images` 生成自包含 HTML；拒绝非 https 的外部协议。
- `validate_report.py` 新增 Figures 检查：零图表或本地图片缺失报错，数量不足、远程图片、缺图注给出警告。

## [2.5.3] - 2026-09-07

### Added

- 统一展示名为「深度研究」，保持调用 ID 与能力契约。

## [2.5.2] - 2026-08-30

### Added

- require an early branching decision guide for comparison, procurement, architecture-choice, and adoption research
- require explicit terminal recommendations and a textual fallback so the decision remains understandable without diagram rendering
- add a strict decision-guide validator and regression tests

## [2.5.1] - 2026-08-30

### Fixed

- render direct HTTP(S) Markdown links as clickable anchors inside report tables and prose
- add regression coverage for shareable repository links and reject non-HTTP URI activation

## [2.5.0] - 2026-08-30

### Added

- add verified open-source solutions landscape workflow
- persist a shareable open_source_solutions.jsonl registry and linked report table
- add strict artifact validation and merge multilingual report validation improvements

## [2.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
