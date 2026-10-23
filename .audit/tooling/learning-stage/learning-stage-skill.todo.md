# learning-stage skill

- [x] Use the **plugin-dev:skill-development** skill (Claude Code's authoring guidance for SKILL.md files).
  - Codex mapping uses skill-creator and writing-for-agents.
- [x] Validate the skill: frontmatter has `name` and `description`, referenced files exist, cross-skill links resolve.
- [x] Test cases if structural.
  - Independent scenarios cover resume, learning evidence, notebook permissions and SPEC handoff.
- [ ] Run **Opening a PR**.
  - skip: no authorization to commit, push or open a PR.

Preserve all existing changes. Deliver only learning-stage and its references.

Validation: Ruby Psych parsed YAML; Python checked metadata, naming, placeholders and relative links. Referenced installed skills exist. Bundled quick_validate.py could not run because both available Python runtimes lack PyYAML; no dependency installed.

Independent forward-test: delegate-claude investigator, session 811ea9c6-cd1c-4066-b2f9-17c6f3610594, model group/light[1m], response model gpt-6-luna. Completed four simulated cases with no warnings. This proves instruction interpretation in those cases, not actual Issue publishing or notebook writes. Report: /private/tmp/learning-stage-evaluation/result.txt.

Later user clarification incorporated: all construction, development and product-experience decision points require corresponding ADRs, alongside learning notes. Explicitly overrides domain-modeling ADR selectivity. Main Agent read back this change and the SPEC coverage check.

Compression pass: preserved requirements, merged prose and replaced verbose template with field list.
SKILL.md: 3484 -> 2388 Unicode characters, 31.5% reduction.
references/records.md: 1298 -> 986 Unicode characters, 24.0% reduction.
references/spec-handoff.md: 1396 -> 1072 Unicode characters, 23.2% reduction.
Total: 6178 -> 4446 Unicode characters, 28.0% reduction. Not a token measurement.
Independent semantic comparison: delegate-claude investigator 2b821af4-e270-4a10-b858-06871d7d02c4, group/light[1m], response gpt-6-luna, completed without warnings. One inferred weakening found: minimum complete explanation; restored explicitly. Main Agent verified relative links independently and all changed files passed whitespace checks. Report: /private/tmp/learning-stage-compression-review/result.txt.

Stage closeout iteration: updated skill and records/SPEC references with phase-feature directories, scoped moves, PR-skill delivery, confirmed main merge and origin/main restart. Structural/link checks passed. Independent scenario check 940cda38-4d11-4c46-9fe8-87d3c80f44f8 completed on group/light[1m], response deepseek-v4.1-flash-free; attempted /tmp report write denied, final read-only report returned. Addressed actionable baseline, authorization and evidence accessibility points; merge receipt pointer had already been corrected. No stage artifact moves, commit or PR performed in this skill-edit task.
