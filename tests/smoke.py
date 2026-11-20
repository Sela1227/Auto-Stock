"""
AutoStock 煙霧測試（唯一驗證入口）

用法：python3 tests/smoke.py
- 非互動、不連正式站、不用權杖、不用 git，10 秒內跑完
- 任何一項失敗回傳非 0（賈維斯與審查員照這支驗收）

檢查項目：
1. Python 語法（app/ 全部）
2. JavaScript 語法（static/ 的 .js 與 HTML 內嵌 <script>；沒有 node 就跳過）
3. FastAPI 啟動 import（裝了 requirements 才跑；攔 NameError 這類語法正確但啟動才炸的錯）
4. API 契約：前端呼叫的每個 /api、/auth 路徑，後端都有對應路由
5. 版號對帳：config.VERSION = CLAUDE.md〇 = README = 版本歷程有這一版；handoff 落後幾版
"""
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAIL: list = []
WARN: list = []


def ok(msg):
    print(f"✓ {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"✗ {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"▲ {msg}")


# ---------------------------------------------------------------------------
# 1. Python 語法
# ---------------------------------------------------------------------------
def check_python():
    bad = []
    files = list((ROOT / "app").rglob("*.py"))
    for p in files:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bad.append(f"{p.relative_to(ROOT)}:{e.lineno} {e.msg}")
    if bad:
        fail("Python 語法：" + "；".join(bad[:5]))
    else:
        ok(f"Python 語法（{len(files)} 檔）")


# ---------------------------------------------------------------------------
# 2. JavaScript 語法
# ---------------------------------------------------------------------------
def check_js():
    node = shutil.which("node")
    if not node:
        warn("沒有 node，跳過 JS 語法檢查")
        return
    bad = []
    js_files = list((ROOT / "static").rglob("*.js"))
    for p in js_files:
        r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
        if r.returncode:
            bad.append(str(p.relative_to(ROOT)))
    inline = 0
    for p in (ROOT / "static").glob("*.html"):
        for i, src in enumerate(re.findall(r"<script>(.*?)</script>", p.read_text(encoding="utf-8"), re.S)):
            inline += 1
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fp:
                fp.write(src)
                tmp = fp.name
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            os.unlink(tmp)
            if r.returncode:
                bad.append(f"{p.name} 內嵌 script #{i}")
    if bad:
        fail("JS 語法：" + "、".join(bad[:5]))
    else:
        ok(f"JS 語法（{len(js_files)} 檔 + {inline} 段內嵌）")


# ---------------------------------------------------------------------------
# 3. FastAPI 啟動 import
# ---------------------------------------------------------------------------
def check_import():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        warn("沒裝 requirements，跳過 FastAPI import 檢查（pip install -r requirements.txt 後會跑）")
        return
    env = dict(os.environ, APP_ENV="development")
    code = "from app.main import app; print(len(app.openapi()['paths']))"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    if r.returncode:
        last = (r.stderr.strip().splitlines() or ["?"])[-1]
        fail(f"FastAPI import 失敗：{last}")
    else:
        ok(f"FastAPI import（OpenAPI {r.stdout.strip().splitlines()[-1]} 個路徑）")


# ---------------------------------------------------------------------------
# 4. API 契約（靜態比對）
# ---------------------------------------------------------------------------
ROUTE_DEC = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*"([^"]*)"')
PREFIX = re.compile(r'APIRouter\(\s*(?:[^)]*?\bprefix\s*=\s*"([^"]*)")?')
MAIN_ROUTE = re.compile(r'@app\.(get|post|put|delete|patch)\(\s*"([^"]*)"')
FRONT_CALL = re.compile(r"""(?:apiRequest|fetch)\(\s*(`[^`]*`|'[^']*'|"[^"]*")""")


def _norm(path: str) -> str:
    path = path.split("?")[0].rstrip("/") or "/"
    return path


def _backend_routes():
    routes = []
    for p in (ROOT / "app" / "routers").glob("*.py"):
        text = p.read_text(encoding="utf-8")
        m = PREFIX.search(text)
        prefix = (m.group(1) or "") if m else ""
        for meth, path in ROUTE_DEC.findall(text):
            routes.append(_norm(prefix + path))
    main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    for meth, path in MAIN_ROUTE.findall(main):
        routes.append(_norm(path))
    # 轉成 regex：{param} 對任一段
    return [re.compile("^" + re.sub(r"\\\{[^}]+\\\}", r"[^/]+", re.escape(r)) + "$") for r in set(routes)]


def _frontend_calls():
    calls = []
    for p in list((ROOT / "static").rglob("*.js")) + list((ROOT / "static").glob("*.html")):
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for raw in FRONT_CALL.findall(line):
                s = raw[1:-1]
                s = re.sub(r"^\$\{[^}]*API_BASE[^}]*\}", "", s)
                s = re.sub(r"\$\{[^}]+\}", "X", s)
                if not (s.startswith("/api/") or s.startswith("/auth/")):
                    continue
                calls.append((f"{p.relative_to(ROOT)}:{i}", _norm(s)))
    return calls


def check_contract():
    routes = _backend_routes()
    calls = _frontend_calls()
    missing = [(where, path) for where, path in calls if not any(r.match(path) for r in routes)]
    if missing:
        fail("前端呼叫的 API 後端沒有：" + "；".join(f"{p}（{w}）" for w, p in missing[:6]))
    else:
        ok(f"API 契約（前端 {len(calls)} 處呼叫都有對應路由）")


# ---------------------------------------------------------------------------
# 5. 版號對帳
# ---------------------------------------------------------------------------
def check_version():
    cfg = (ROOT / "app" / "config.py").read_text(encoding="utf-8")
    m = re.search(r"""^VERSION\s*=\s*['"](V\d+\.\d+\.\d+)['"]""", cfg, re.M)
    if not m:
        fail("app/config.py 找不到 VERSION = 'V…'")
        return
    v = m.group(1)
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    cv = re.search(r"\*\*版本[:：]\*\*\s*(V\d+\.\d+\.\d+)", claude)
    rv = re.search(r"目前版本[:：]\s*(V\d+\.\d+\.\d+)", readme)
    problems = []
    if not cv or cv.group(1) != v:
        problems.append(f"CLAUDE.md〇是 {cv.group(1) if cv else '無'}")
    if not rv or rv.group(1) != v:
        problems.append(f"README 是 {rv.group(1) if rv else '無'}")
    history = claude.split("## 六", 1)[-1] if "## 六" in claude else ""
    rows = re.findall(r"^\|\s*(V\d+\.\d+\.\d+)\s*\|", history, re.M)
    if v not in rows:
        problems.append("CLAUDE.md 版本歷程沒有這一版")
    for js in ("static/js/core.js", "static/index.html"):
        if re.search(r"""['"`]v['"`]\s*\+\s*\(?data\.version|`v\$\{version\}`""", (ROOT / js).read_text(encoding="utf-8")):
            problems.append(f"{js} 自己在版號前加 v，畫面會跟 VERSION 不一致")
    if problems:
        fail(f"版號對帳（VERSION={v}）：" + "；".join(problems))
    else:
        ok(f"版號對帳 {v}（config = CLAUDE.md = README = 版本歷程）")

    hf = ROOT / "SELA-handoff.md"
    if not hf.exists():
        warn("沒有 SELA-handoff.md")
        return
    hv = re.search(r"完成版本[^V]*(V\d+\.\d+\.\d+)", hf.read_text(encoding="utf-8"))
    if not hv:
        warn("SELA-handoff.md 讀不到完成版本")
    elif hv.group(1) in rows:
        behind = rows.index(hv.group(1))
        (warn if behind > 5 else ok)(f"handoff 停在 {hv.group(1)}（落後 {behind} 版）")
    else:
        warn(f"handoff 的 {hv.group(1)} 不在版本歷程表內（已過期）")


if __name__ == "__main__":
    print(f"AutoStock 煙霧測試 — {ROOT.name}")
    check_python()
    check_js()
    check_import()
    check_contract()
    check_version()
    print(f"\n結果：{len(FAIL)} 項失敗、{len(WARN)} 項提醒")
    sys.exit(1 if FAIL else 0)
