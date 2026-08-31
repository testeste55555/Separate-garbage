#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "app/app.js"
CSS = ROOT / "app/styles.css"
VALIDATOR = ROOT / "scripts/validate_lesson_box_style_resolver.py"
RED_TEAM = ROOT / "scripts/red_team_lesson_box_style_resolver.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing expected {label} block")
    if text.count(old) != 1:
        raise SystemExit(f"expected one {label} block, found {text.count(old)}")
    return text.replace(old, new, 1)


def patch_js() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''  function displayColumns(count) {\n    if (count <= 2) return count || 1;\n    if (count <= 4) return 2;\n    if (count <= 6) return 3;\n    if (count <= 12) return 4;\n    return 5;\n  }''',
        '''  function displayColumns(count) {\n    if (count <= 2) return count || 1;\n    if (count <= 4) return 2;\n    if (count <= 9) return 3;\n    return 4;\n  }''',
        "displayColumns",
    )
    text = replace_once(
        text,
        '    for (const row of rows) {\n      const usesTeachingBox = Boolean(row.teaching_box_id?.trim());',
        '    for (const [boxIndex, row] of rows.entries()) {\n      const usesTeachingBox = Boolean(row.teaching_box_id?.trim());',
        "bucket loop",
    )
    text = replace_once(
        text,
        '''      box.classList.add(OFFICIAL_STYLE_STATUSES.has(status) ? "bucket--official-style" : "bucket--fallback-style");\n\n      if (interactive) {''',
        '''      if (OFFICIAL_STYLE_STATUSES.has(status)) {\n        box.classList.add("bucket--official-style");\n      } else {\n        box.classList.add("bucket--fallback-style");\n        box.dataset.fallbackPalette = String((boxIndex % 8) + 1);\n      }\n\n      if (interactive) {''',
        "fallback palette assignment",
    )
    APP_JS.write_text(text, encoding="utf-8")


def patch_css() -> None:
    text = CSS.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''.bucket-grid {\n  display: grid;\n  gap: 16px;\n}''',
        '''.bucket-grid {\n  display: grid;\n  gap: 20px;\n}''',
        "bucket grid",
    )
    text = replace_once(
        text,
        '''.bucket {\n  min-height: 170px;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  text-align: center;\n  padding: 18px;\n  background: #fff;\n  border: 5px solid #222;\n  border-radius: 12px;\n  font-size: clamp(28px, 4vw, 54px);\n  font-weight: 800;\n  line-height: 1.15;\n  line-break: strict;\n  overflow-wrap: anywhere;\n  text-wrap: balance;\n}''',
        '''.bucket {\n  min-height: 220px;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  text-align: center;\n  padding: 24px 28px;\n  background: #fff;\n  border: 6px solid #222;\n  border-radius: 14px;\n  font-size: clamp(38px, 4.6vw, 70px);\n  font-weight: 850;\n  line-height: 1.12;\n  line-break: strict;\n  overflow-wrap: anywhere;\n  text-wrap: balance;\n}''',
        "bucket size",
    )
    text = replace_once(
        text,
        '''.bucket--compact { font-size: clamp(25px, 3.4vw, 48px); }\n.bucket--long { font-size: clamp(21px, 2.7vw, 38px); line-height: 1.2; }\n.bucket--neutral-style,\n.bucket--fallback-style {\n  background-color: #e8edf2;\n  background-image: repeating-linear-gradient(\n    135deg,\n    rgb(255 255 255 / 22%) 0,\n    rgb(255 255 255 / 22%) 12px,\n    rgb(31 41 55 / 7%) 12px,\n    rgb(31 41 55 / 7%) 24px\n  );\n  border-color: #273746;\n  color: #111;\n}\n\n.bucket--fallback-style[data-box-kind="SIMPLIFIED_ACTION"] {\n  border-style: dashed;\n  background-image: repeating-linear-gradient(\n    45deg,\n    rgb(255 255 255 / 28%) 0,\n    rgb(255 255 255 / 28%) 10px,\n    rgb(31 41 55 / 9%) 10px,\n    rgb(31 41 55 / 9%) 20px\n  );\n}''',
        '''.bucket--compact { font-size: clamp(32px, 3.8vw, 58px); }\n.bucket--long { font-size: clamp(27px, 3.1vw, 48px); line-height: 1.16; }\n.bucket--neutral-style,\n.bucket--fallback-style {\n  background-color: #FFE082;\n  background-image: none;\n  border-color: #6D4C00;\n  border-style: solid;\n  color: #111;\n}\n\n.bucket--fallback-style[data-fallback-palette="1"] { background-color: #FFE082; border-color: #6D4C00; }\n.bucket--fallback-style[data-fallback-palette="2"] { background-color: #90CAF9; border-color: #0D47A1; }\n.bucket--fallback-style[data-fallback-palette="3"] { background-color: #A5D6A7; border-color: #1B5E20; }\n.bucket--fallback-style[data-fallback-palette="4"] { background-color: #F8BBD0; border-color: #880E4F; }\n.bucket--fallback-style[data-fallback-palette="5"] { background-color: #D1C4E9; border-color: #4527A0; }\n.bucket--fallback-style[data-fallback-palette="6"] { background-color: #FFCC80; border-color: #E65100; }\n.bucket--fallback-style[data-fallback-palette="7"] { background-color: #B2EBF2; border-color: #006064; }\n.bucket--fallback-style[data-fallback-palette="8"] { background-color: #CFD8DC; border-color: #263238; }\n\n.bucket--fallback-style[data-box-kind="SIMPLIFIED_ACTION"] {\n  border-style: dashed;\n}''',
        "fallback styles",
    )
    text = replace_once(
        text,
        '''body.presentation-mode .bucket-grid { grid-auto-rows: 1fr; }\nbody.presentation-mode .bucket {\n  min-height: 0;\n  border-width: 6px;\n  border-radius: 14px;\n  font-size: clamp(30px, 4.2vw, 68px);\n}\nbody.presentation-mode .bucket--compact { font-size: clamp(27px, 3.6vw, 56px); }\nbody.presentation-mode .bucket--long { font-size: clamp(22px, 2.8vw, 44px); }''',
        '''body.presentation-mode .bucket-grid {\n  grid-auto-rows: minmax(220px, 1fr);\n  gap: 20px;\n}\nbody.presentation-mode .bucket {\n  min-height: 220px;\n  padding: 22px 26px;\n  border-width: 7px;\n  border-radius: 16px;\n  font-size: clamp(44px, 5vw, 82px);\n}\nbody.presentation-mode .bucket--compact { font-size: clamp(36px, 4.1vw, 66px); }\nbody.presentation-mode .bucket--long { font-size: clamp(30px, 3.3vw, 54px); }''',
        "presentation bucket styles",
    )
    CSS.write_text(text, encoding="utf-8")


def patch_validator() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''        '"bucket--fallback-style"',\n    }''',
        '''        '"bucket--fallback-style"', "box.dataset.fallbackPalette",\n    }''',
        "validator required js",
    )
    text = replace_once(
        text,
        '''        if "repeating-linear-gradient" not in body or "border-color" not in body:\n            errors.append("fallback style lacks pattern or strong border")''',
        '''        if "background-image: none" not in body or "border-color" not in body or "border-style: solid" not in body:\n            errors.append("fallback style lacks solid high-contrast surface")\n        palette_rules = re.findall(r'\\.bucket--fallback-style\\[data-fallback-palette="[1-8]"\\]', css)\n        if len(palette_rules) != 8:\n            errors.append("fallback palette does not define all 8 classroom colors")''',
        "validator fallback rule",
    )
    VALIDATOR.write_text(text, encoding="utf-8")


def patch_red_team() -> None:
    text = RED_TEAM.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''        ("fallback surface returned to white", lambda root: replace(root, "app/styles.css", "background-color: #e8edf2;", "background-color: #ffffff;")),\n        ("fallback pattern removed", lambda root: replace(root, "app/styles.css", "background-image: repeating-linear-gradient(", "background-image: linear-gradient(")),''',
        '''        ("fallback surface returned to white", lambda root: replace(root, "app/styles.css", "background-color: #FFE082;", "background-color: #ffffff;")),\n        ("fallback palette assignment removed", lambda root: replace(root, "app/app.js", "box.dataset.fallbackPalette = String((boxIndex % 8) + 1);", "")),''',
        "red team fallback mutations",
    )
    RED_TEAM.write_text(text, encoding="utf-8")


def main() -> None:
    patch_js()
    patch_css()
    patch_validator()
    patch_red_team()
    print("CLASSROOM_PROJECTION_UI_FIX_APPLIED")


if __name__ == "__main__":
    main()
