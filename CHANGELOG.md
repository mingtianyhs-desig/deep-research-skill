# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.7.0] - 2026-10-28

### Changed

- **BREAKING**: 研究报告产出位置从 `~/Documents/[Topic]_Research_[YYYYMMDD]/` 改为相对当前工作目录的 `research/[主题]_研究_[YYYYMMDD]/`。切换工作区时产出自动跟随，不再写入用户主目录或技能安装目录。
- 移除 `~/.claude/research_output/` 内部 tracking 副本。续写状态文件 `continuation_state_*.json` 改为跟随报告所在目录，避免同一产物出现两个权威副本。
- `research_engine.py` 的输出目录由 `Path.home()/".claude"/"research_output"` 改为 `Path.cwd()/"research"`，并新增 `--out-dir` 参数可覆盖默认值。
- `citation_manager.py init-run` 的 `--out-dir` 改为可选：省略时由 `--query` 解析运行目录，调用方不再需要手工拼路径。
- 路径约定不再依赖文档描述，改由 `citation_manager.py` 承载；文档只保留调用方式。

### Added

- `citation_manager.py` 新增 `slugify_topic()` / `resolve_run_dir()` / `check_run_dir()`：主题清洗（非法字符与路径分隔符转下划线、保留 CJK、60 字符截断）、中文 `研究` 后缀、`YYYYMMDD` 日期、同名目录 `_2`/`_3` 后缀。
- `validate_report.py` 新增 Output Location 检查：报告不在 `research/<主题>_研究_<YYYYMMDD>/` 内时给出告警。该检查复用 `check_run_dir()`，不重复实现命名规则。
- `tests/test_citation_manager.py` 新增 13 个运行目录用例，`tests/test_validate_report.py` 新增 5 个 Output Location 用例，覆盖路径穿越防护、中文保留、碰撞后缀与门禁双向行为。

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
