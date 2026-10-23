from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
plan = root / "docs/plans/roadmap/sayhear-build-and-learning-plan.md"
research = root / "docs/plans/roadmap/sayhear-route-research.md"
text = plan.read_text()
sections = re.split(r"(?m)^## 阶段 ", text)[1:]
assert len(sections) == 6, f"阶段数量不符，实际为 {len(sections)}"
required = [
    "### Feature & spec",
    "### 验收标准",
    "### 学习活动与理解证据",
    "### 待确认问题",
]
for section in sections:
    for heading in required:
        assert heading in section, f"{section.splitlines()[0]} 缺少 {heading}"
    print(f"PASS 阶段 {section.splitlines()[0]}")

budget_block = text.split("## 年底阶段顺序与预算", 1)[1].split("## 阶段 0", 1)[0]
rows = re.findall(r"(?m)^\| (?:[0-5]\. [^|]+|共用缓冲) \| (\d+) 小时 \|", budget_block)
assert len(rows) == 7, f"预算明细应为七行，实际为 {len(rows)}"
assert sum(map(int, rows)) == 100, rows
print("PASS 预算明细为 100 小时。")

for file in [plan, research]:
    content = file.read_text()
    assert "—" not in content, f"{file} 包含长破折号"
    assert "file://" not in content, f"{file} 包含 file URI"
    for target in re.findall(r"\]\(([^)]+)\)", content):
        target = target.strip("<>")
        if target.startswith(("https://", "http://", "#")):
            continue
        resolved = (file.parent / target.split("#", 1)[0]).resolve()
        assert resolved.exists(), f"本地链接不存在 {target}"
    print(f"PASS {file.name} 的本地链接及基础格式。")

assert "Proposed" in text
assert "尚未执行" in text
assert all(name in text for name in ["Reflection", "Provider", "canonical", "测试库", "清理"])
print("PASS 状态与核心边界字段。结构检查不验证事实、体验或实现效果。")
