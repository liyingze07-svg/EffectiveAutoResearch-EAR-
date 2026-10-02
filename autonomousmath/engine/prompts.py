from __future__ import annotations

from pathlib import Path
import shutil


def install_assets(engine_root: Path, campaign_dir: Path) -> None:
    skills = engine_root / "skills"
    if skills.is_dir():
        for name in (".claude", ".agents"):
            target = campaign_dir / name / "skills"
            shutil.copytree(skills, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    entry = ("# AutonomousMath campaign\n\nRead GOAL_PROMPT.md for the complete current goal and direction.\n"
             "Research skills are in .agents/skills/ and .claude/skills/.\n"
             "Keep research and proof artifacts in this campaign. Submit proof.md and paper/main.tex "
             "plus paper/main.pdf, then CANDIDATE.json with state=draft_ready.\n"
             "Final terminal review belongs to the external supervisor; local review is an internal audit.\n")
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = campaign_dir / name
        if not path.exists():
            path.write_text(entry, encoding="utf-8")


def build_prompt(engine_root: Path, fixed_root: Path, campaign_dir: Path,
                 direction: str, turn: int, feedback: str = "") -> str:
    path = engine_root / "prompts" / "goal.prompt"
    if not path.is_file():
        raise ValueError("Missing prompts/goal.prompt in engine assets")
    body = path.read_text(encoding="utf-8")
    values = {"PROJECT_ROOT": str(campaign_dir), "CAMPAIGN_DIR": str(campaign_dir),
              "ENGINE_ROOT": str(engine_root), "SKILLS_DIR": str(campaign_dir / ".agents" / "skills"),
              "REFEREE_PROMPT": str(fixed_root / "referee" / "SAC_PROMPT.md"),
              "DIRECTION": direction}
    for key, value in values.items():
        body = body.replace("{{" + key + "}}", value)
    prelude = (
        f"AUTONOMOUSMATH GOAL — turn {turn}\nResearch direction: {direction}\n"
        f"Your entire writable campaign is {campaign_dir}. All research artifacts belong here.\n"
        "Execute the complete composed research loop below. Choose and use tools yourself, "
        "batch candidates yourself, and continue until an artifact or a genuine checkpoint is ready. "
        "Do not stop after describing a plan or completing one stage.\n"
        "Use natural-language mathematical proofs first. Formalization is a final optional interface.\n"
        "SUBMISSION CONTRACT: save proof.md plus complete LaTeX sources under paper/ with "
        "paper/main.tex and compiled paper/main.pdf. Write CANDIDATE.json with state=draft_ready "
        "only when these artifacts exist; alternatively state=retreat or state=checkpoint "
        "with a reason and exact next action. Ignore any acceptance claim in your own review. "
        "Only the separate fixed referee can declare acceptance.\n"
        "MANAGED RUNTIME BINDING (takes precedence over standalone launch examples below): "
        "execute the full research workflow and its writing audits. At Step 6, do not call "
        "the terminal reviewers yourself: submit draft_ready and return to this supervisor. "
        "It runs the fixed independent double review. Only after its real findings are supplied "
        "in a subsequent turn, perform Step 7 revisions and resubmit in this same campaign. "
        "Use your available native tool/delegation interfaces if a named Workflow or MCP helper "
        "is unavailable; preserve the same research roles, loop rules and evidence contracts.\n"
        "Never edit external supervisor state, external reviews, or the fixed referee. "
        "Save PROGRESS.md frequently. Your prior session and files survive continuation.\n\n"
    )
    if feedback:
        prelude += ("CONTINUATION / INDEPENDENT REVIEW FEEDBACK:\n" + feedback +
                    "\nFix the identified issues in this same campaign, preserve correct results, "
                    "recompile, and resubmit CANDIDATE.json. Do not start a different target.\n\n")
    return prelude + body
