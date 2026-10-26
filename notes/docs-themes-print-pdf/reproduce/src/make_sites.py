"""Write one identical print fixture into each generator's native source format.

Usage: python3 -I make_sites.py OUT_DIR
Each arm gets OUT_DIR/<arm>/ with the generator's sources; build.sh builds them.
Sentinels (ZQ*) are the readout: CTRL ones must print visibly, the rest are the tested mechanisms.
"""
import sys
from pathlib import Path

LONG_CMD = ("curl -X POST https://api.example.com/v1/projects/acme-production/deployments "
            "-H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN' "
            "-d '{\"ref\":\"main\",\"environment\":\"production\",\"auto_merge\":false,\"required_contexts\":[]}' "
            "ZQCODEEND")
LONG_URL = ("https://downloads.example.com/releases/stable/linux-x86_64/package?"
            "version=2026.10.26&checksum=sha256_9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
            "&mirror=primaryZQURLEND")
HEAD = ["Option", "Type", "Default", "Environment variable", "Since", "Applies to", "Example value"]
ROW = ["``ZQTABLECTRL``", "``integer_or_null``", "``max_connection_pool_size``", "``ACME_MAX_CONNECTION_POOL_SIZE``",
       "``v2026.10.0_preview``", "``worker_and_scheduler_processes``", "``ZQTABLEEND``"]
P_INTRO = ("This page is a print fixture. Each block below holds a marker word that must appear on paper. "
           "First marker: ZQPARACTRL.")
P_URL = "Download the release from " + LONG_URL + " and verify it."
P_TAB1 = "Run the Linux installer. ZQTAB1CTRL"
P_TAB2 = "Run the Windows installer. ZQTAB2"
P_DET = "Additional troubleshooting notes. ZQDETAILS"
P_END = "Last paragraph of the page. ZQENDCTRL"


def md_table():
    row = [c.replace("``", "`") for c in ROW]
    return "| " + " | ".join(HEAD) + " |\n|" + "---|" * len(HEAD) + "\n| " + " | ".join(row) + " |\n"


def md_body(tabs: str, details: str) -> str:
    return (f"{P_INTRO}\n\n```bash\nZQCODECTRL\n{LONG_CMD}\n```\n\n{md_table()}\n{P_URL}\n\n"
            f"{tabs}{details}{P_END}\n")


HTML_DETAILS = f"<details>\n<summary>Show more</summary>\n\n{P_DET}\n\n</details>\n\n"


def docusaurus(d: Path):
    body = md_body(
        "<Tabs>\n<TabItem value=\"linux\" label=\"Linux\" default>\n\n" + P_TAB1 + "\n\n</TabItem>\n"
        "<TabItem value=\"windows\" label=\"Windows\">\n\n" + P_TAB2 + "\n\n</TabItem>\n</Tabs>\n\n",
        HTML_DETAILS)
    w(d / "docs/fixture.mdx", "---\ntitle: Print fixture\n---\n\nimport Tabs from '@theme/Tabs';\n"
      "import TabItem from '@theme/TabItem';\n\n" + body)


def starlight(d: Path):
    body = md_body(
        "<Tabs>\n<TabItem label=\"Linux\">\n\n" + P_TAB1 + "\n\n</TabItem>\n"
        "<TabItem label=\"Windows\">\n\n" + P_TAB2 + "\n\n</TabItem>\n</Tabs>\n\n",
        HTML_DETAILS)
    w(d / "src/content/docs/fixture.mdx", "---\ntitle: Print fixture\n---\n\n"
      "import { Tabs, TabItem } from '@astrojs/starlight/components';\n\n" + body)


def vitepress(d: Path):
    body = md_body(
        "::: code-group\n\n```sh [Linux]\n" + P_TAB1 + "\n```\n\n```sh [Windows]\n" + P_TAB2 + "\n```\n\n:::\n\n",
        "::: details Show more\n" + P_DET + "\n:::\n\n")
    w(d / "docs/fixture.md", "# Print fixture\n\n" + body)
    w(d / "docs/.vitepress/config.mjs", "export default { title: 'Fixture' }\n")
    w(d / "docs/index.md", "# Home\n\n[Fixture](./fixture)\n")


def mkdocs_material(d: Path):
    ind = lambda s: "\n".join("    " + l if l else "" for l in s.splitlines())
    body = md_body(
        "=== \"Linux\"\n\n" + ind(P_TAB1) + "\n\n=== \"Windows\"\n\n" + ind(P_TAB2) + "\n\n",
        "??? note \"Show more\"\n\n" + ind(P_DET) + "\n\n")
    w(d / "docs/fixture.md", "# Print fixture\n\n" + body)
    w(d / "docs/index.md", "# Home\n")
    w(d / "mkdocs.yml", "site_name: Fixture\ntheme:\n  name: material\nmarkdown_extensions:\n"
      "  - admonition\n  - pymdownx.details\n  - pymdownx.superfences\n  - pymdownx.tabbed:\n"
      "      alternate_style: true\n  - tables\n")


def mkdocs_default(d: Path):
    w(d / "docs/fixture.md", "# Print fixture\n\n" + md_body("", HTML_DETAILS))
    w(d / "docs/index.md", "# Home\n")
    w(d / "mkdocs.yml", "site_name: Fixture\ntheme:\n  name: mkdocs\n")


def mdbook(d: Path):
    w(d / "src/fixture.md", "# Print fixture\n\n" + md_body("", HTML_DETAILS))
    w(d / "src/SUMMARY.md", "# Summary\n\n- [Print fixture](./fixture.md)\n")
    w(d / "book.toml", "[book]\ntitle = \"Fixture\"\n")


def sphinx(d: Path, theme: str):
    def ind(s, n=3):
        return "\n".join(" " * n + l if l else "" for l in s.splitlines())
    rows = "   * - " + "\n     - ".join(HEAD) + "\n   * - " + "\n     - ".join(ROW) + "\n"
    rst = (f"Print fixture\n=============\n\n{P_INTRO}\n\n.. code-block:: bash\n\n   ZQCODECTRL\n   {LONG_CMD}\n\n"
           f".. list-table::\n   :header-rows: 1\n\n{rows}\n{P_URL}\n\n"
           f".. tab-set::\n\n   .. tab-item:: Linux\n\n{ind(P_TAB1, 6)}\n\n   .. tab-item:: Windows\n\n{ind(P_TAB2, 6)}\n\n"
           f".. dropdown:: Show more\n\n{ind(P_DET)}\n\n{P_END}\n")
    w(d / "fixture.rst", rst)
    w(d / "index.rst", "Home\n====\n\n.. toctree::\n\n   fixture\n")
    w(d / "conf.py", f"project = 'Fixture'\nextensions = ['sphinx_design']\nhtml_theme = '{theme}'\n")


def baseline(d: Path):
    """G0: browser default stylesheet, no theme; also carries the instrument controls."""
    import html
    cells = lambda r, t: "".join(f"<{t}><code>{html.escape(c.strip('`'))}</code></{t}>" if '`' in c
                                 else f"<{t}>{html.escape(c)}</{t}>" for c in r)
    page = ("<!doctype html><html lang=en><meta charset=utf-8><title>Print fixture</title>\n<h1>Print fixture</h1>\n"
            f"<p>{P_INTRO}</p>\n<pre><code>ZQCODECTRL\n{html.escape(LONG_CMD)}</code></pre>\n"
            f"<table><thead><tr>{cells(HEAD, 'th')}</tr></thead><tbody><tr>{cells(ROW, 'td')}</tr></tbody></table>\n"
            f"<p>{html.escape(P_URL)}</p>\n<details><summary>Show more</summary><p>{P_DET}</p></details>\n"
            f"<p>{P_END}</p>\n"
            # instrument controls: clipped text must read CLIPPED, display:none must read MISSING
            "<div style=\"width:60px;overflow:hidden;white-space:nowrap\">xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ZQCLIPCTRL</div>\n"
            "<span style=\"display:none\">ZQHIDDENCTRL</span>\n</html>\n")
    w(d / "index.html", page)
    # positive control: same page, code wrapped -> ZQCODEEND must read VISIBLE
    w(d.parent / "g0-prewrap" / "index.html",
      page.replace("<pre>", "<pre style=\"white-space:pre-wrap;overflow-wrap:anywhere\">"))


def w(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    out = Path(sys.argv[1])
    docusaurus(out / "docusaurus")
    starlight(out / "starlight")
    vitepress(out / "vitepress")
    mkdocs_material(out / "mkdocs-material")
    mkdocs_default(out / "mkdocs")
    mdbook(out / "mdbook")
    for t in ("alabaster", "furo", "sphinx_rtd_theme", "pydata_sphinx_theme"):
        sphinx(out / f"sphinx-{t.replace('_', '-')}", t)
    baseline(out / "g0")
    print("ok", sorted(p.name for p in out.iterdir()))
