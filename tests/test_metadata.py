from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "freestocklineskill"


def skill_frontmatter() -> str:
    source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    return source.split("---", 2)[1]


def test_skill_metadata_targets_openclaw_and_has_no_required_env():
    source = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_frontmatter()

    assert "name: freestocklineskill" in source
    assert 'version: "0.1.0"' in source
    assert "openclaw" in source
    assert 'bins: ["python3"]' in source
    assert "OPENAI_API_KEY" not in source
    assert "primaryEnv" not in source
    assert "\n    env:" not in frontmatter
    assert "required_env" not in frontmatter
    assert "requires:\n      bins" in source


def test_agent_metadata_uses_requested_display_name():
    source = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert 'display_name: "freeStockLIneskill"' in source
    assert "smart-query" in source


def test_use_cases_contains_at_least_100_numbered_examples():
    source = (SKILL_DIR / "references" / "use-cases.md").read_text(encoding="utf-8")
    numbered = [line for line in source.splitlines() if line.strip() and line.split(".", 1)[0].isdigit()]

    assert len(numbered) >= 100


def test_readme_documents_openclaw_hermes_and_clawhub():
    source = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "OpenClaw" in source
    assert "Hermes" in source
    assert "clawhub publish freestocklineskill" in source


def test_no_runtime_requires_user_api_key_or_token():
    scanned_files = [
        *SKILL_DIR.glob("scripts/**/*.py"),
        ROOT / "scripts" / "install_skill.sh",
        ROOT / "scripts" / "validate_skill.sh",
        ROOT / "pyproject.toml",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in scanned_files)

    assert "OPENAI_API_KEY" not in combined
    assert "TUSHARE_TOKEN" not in combined
    assert "TUSHARE_API_KEY" not in combined
    assert "AKSHARE_TOKEN" not in combined
    assert "EFINANCE_TOKEN" not in combined
    assert "api_key" not in combined.lower()
    assert "apikey" not in combined.lower()
    assert "Authorization" not in combined
    assert "Bearer" not in combined


def test_docs_explicitly_commit_to_free_broad_a_share_coverage():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "不需要用户输入任何 apikey/API Key" in readme
    assert "不需要用户输入任何 apikey/API Key" in skill
    for keyword in ["股票", "指数", "ETF/LOF", "可转债", "板块", "资金流", "财务", "公告", "龙虎榜"]:
        assert keyword in readme
        assert keyword in skill
