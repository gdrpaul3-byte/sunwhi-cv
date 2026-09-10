#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Business card in the lab website's terminal style.

    python scripts/render_card.py            # -> build-private/card/

Writes, into the git-ignored build-private/card/ (the card carries the
personal mobile number from private.yaml):

    card-print.pdf   2 pages, 92 x 52 mm = 90 x 50 mm trim + 1 mm bleed, vector text
    card-front.png   trimmed 90 x 50 mm at 600 dpi
    card-back.png    trimmed 90 x 50 mm at 600 dpi
    card-preview.png both faces side by side, for a quick look
    card.html        the source the PDF and PNGs were rendered from

Every run checks its own output and exits non-zero if any check fails:
  - the web fonts actually loaded (a silent fallback would ship Courier New);
  - every Hangul glyph exists in the Korean font;
  - no text crosses into the 3 mm safety margin inside the trim line;
  - the QR code decodes to the lab URL at print resolution, as a blurred and
    JPEG-compressed phone photo, and at 200 dpi.

Needs Playwright (Python) and an installed Chrome; qrcode, Pillow, OpenCV and
fontTools for generation and checks.
"""
from __future__ import annotations

import argparse
import glob
import html
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cvdata  # noqa: E402

OUT = os.path.join(cvdata.ROOT, "build-private", "card")

TRIM_W, TRIM_H = 90.0, 50.0     # Korean standard card, mm
BLEED = 1.0                     # per side — most Korean print shops ask 92 x 52
SAFE = 3.0                      # keep text this far inside the trim line
QR_MM = 17.0                    # code size; ~scan distance / 10 is the usual floor
DPI = 600
MM_PX = 96 / 25.4               # CSS px per mm

# The lab site's palette. Its translucent tokens (#00ff4133, #00ff4188) are
# flattened onto the background here, because alpha is unpredictable in print.
C = {
    "bg": "#020b02", "bg_card": "#040f04",
    "green": "#00ff41", "dim": "#00bb30", "amber": "#ffb300",
    "rule": "#023c0f",      # --border        flattened
    "rule_hi": "#018d24",   # --border-bright flattened
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


# --------------------------------------------------------------------------
# QR
# --------------------------------------------------------------------------

def qr_svg(url: str) -> tuple[str, int]:
    """SVG markup for the QR modules (no quiet zone — the panel provides it)."""
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    d = "".join("M%d %dh1v1h-1z" % (x, y)
                for y, row in enumerate(m) for x, on in enumerate(row) if on)
    svg = ('<svg viewBox="0 0 %d %d" shape-rendering="crispEdges" '
           'xmlns="http://www.w3.org/2000/svg"><path fill="%s" d="%s"/></svg>'
           % (n, n, C["bg"], d))
    return svg, n


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------

def card_data(d: dict) -> dict:
    p, c = d["person"], d.get("card") or {}
    if not c:
        raise cvdata.CVError("cv.yaml has no `card:` block")
    url = (p.get("links") or {}).get(c.get("link", "lab"))
    if not url:
        raise cvdata.CVError("card.link %r is not a key in person.links" % c.get("link"))
    name_en = c.get("name_en") or p.get("name_en", "")
    parts = [s.strip() for s in name_en.split(",")]
    boot_name = " ".join(x.upper() for x in parts[:2]) + (", " + parts[2] if len(parts) > 2 else "")
    shown = url.split("//", 1)[-1].rstrip("/")
    host, _, path = shown.partition("/")
    addr_en = c.get("address_en") or []
    if isinstance(addr_en, str):
        addr_en = [addr_en]
    return {
        "name_kr": p.get("name_kr", ""),
        "name_en": name_en,
        "boot_name": boot_name,
        "role_kr": c.get("role_kr", ""),
        "dept_kr": c.get("dept_kr", ""),
        "role_en": c.get("role_en", ""),
        "mobile": (p.get("phones") or {}).get("mobile"),
        "tel": c.get("tel"), "fax": c.get("fax"),
        "email": c.get("email") or (p.get("emails") or [""])[0],
        "postcode": c.get("postcode", ""),
        "address_kr": c.get("address_kr", ""),
        "address_en": addr_en,
        "institution_kr": p.get("institution_kr", ""),
        "institution_en": p.get("institution_en", ""),
        "url": url,
        "url_lines": [host + "/", path] if path else [host],
    }


def build_html(k: dict, qr: str, qr_modules: int,
               face_w: float = TRIM_W + 2 * BLEED,
               face_h: float = TRIM_H + 2 * BLEED) -> str:
    """Design against a 90 x 50 trim box centred in a face of any size.

    Chrome snaps PDF page sizes to its own grid (92 x 52 mm comes out
    92.117 x 51.901), so the face is sized to what Chrome will really produce
    and everything positions from the trim, not from the page edge.
    """
    pad = SAFE + 0.4                  # a hair inside the safe line, from the trim
    module = QR_MM / qr_modules       # fixed code size, whatever the version
    quiet = 4 * module                # the spec's 4-module quiet zone

    contacts = [("M", k["mobile"]), ("T", k["tel"]), ("E", k["email"]), ("F", k["fax"])]
    contacts = [(a, b) for a, b in contacts if b]
    contact_html = "".join('<div><span class="k">%s</span>%s</div>' % (esc(a), esc(b))
                           for a, b in contacts)

    css = """
@page { size: %(fw).3fmm %(fh).3fmm; margin: 0; }
:root {
  --bg: %(bg)s; --bg-card: %(bg_card)s; --green: %(green)s; --dim: %(dim)s;
  --amber: %(amber)s; --rule: %(rule)s; --rule-hi: %(rule_hi)s;
  --mono: 'Share Tech Mono', 'Noto Sans KR', 'Noto Sans CJK KR', 'Malgun Gothic', monospace;
  --vt: 'VT323', 'Noto Sans KR', monospace;
  --kr: 'Noto Sans KR', 'Noto Sans CJK KR', 'Malgun Gothic', sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #3a3f3a; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact;
       word-break: keep-all; -webkit-font-smoothing: antialiased; }
.face {
  width: %(fw).3fmm; height: %(fh).3fmm; position: relative; overflow: hidden;
  background: radial-gradient(120%% 90%% at 12%% 8%%, var(--bg-card) 0%%, var(--bg) 60%%);
  color: var(--green); font-family: var(--mono);
  margin: 0 0 8mm 0;
}
.trim { position: absolute; left: %(tx).3fmm; top: %(ty).3fmm;
        width: %(tw).1fmm; height: %(th).1fmm; }
.safe { position: absolute; inset: %(pad).2fmm; display: flex; flex-direction: column; }

/* HUD corner ticks at the safe line — the site's terminal frame, print-safe */
.tick { position: absolute; width: 2.2mm; height: 2.2mm; border-color: var(--rule-hi);
        border-style: solid; border-width: 0; }
.tick.tl { top: %(tk).2fmm; left: %(tk).2fmm; border-top-width: .22mm; border-left-width: .22mm; }
.tick.tr { top: %(tk).2fmm; right: %(tk).2fmm; border-top-width: .22mm; border-right-width: .22mm; }
.tick.bl { bottom: %(tk).2fmm; left: %(tk).2fmm; border-bottom-width: .22mm; border-left-width: .22mm; }
.tick.br { bottom: %(tk).2fmm; right: %(tk).2fmm; border-bottom-width: .22mm; border-right-width: .22mm; }

/* front ---------------------------------------------------------------- */
.bar { display: flex; justify-content: space-between; align-items: baseline;
       font-family: var(--vt); font-size: 11pt; line-height: 1;
       padding-bottom: 1.2mm; border-bottom: .2mm solid var(--rule-hi); }
.bar .logo b { color: var(--dim); font-weight: normal; }
.bar .inst { color: var(--dim); letter-spacing: .08em; }
.name { margin-top: 3.4mm; }
.name .kr { font-family: var(--kr); font-weight: 700; font-size: 17pt; line-height: 1.05;
            letter-spacing: -.02em; }
.name .en { font-family: var(--vt); font-size: 13.5pt; line-height: 1; margin-top: 1mm; }
.cursor { display: inline-block; width: .5em; height: .82em; margin-left: .15em;
          background: var(--green); vertical-align: -.06em; }
.meta { margin-top: 3mm; font-size: 6.6pt; line-height: 1.62; }
.meta .row { display: flex; }
.meta .key { color: var(--dim); width: 7ch; flex: none; }
.meta .val { color: var(--green); }
.meta .val.sub { color: var(--dim); }
.contact { margin-top: auto; display: grid; grid-template-columns: 1fr 1fr;
           column-gap: 3mm; font-size: 7pt; line-height: 1.6; }
.contact .k { color: var(--dim); display: inline-block; width: 2.1ch; }

/* back ----------------------------------------------------------------- */
.boot { font-size: 5.8pt; line-height: 1.55; color: var(--dim); }
.boot .g { color: var(--green); }
.boot .a { color: var(--amber); }
.link { display: flex; align-items: center; gap: 3.2mm; margin-top: 2.6mm; }
.qr { flex: none; background: var(--green); padding: %(quiet).3fmm;
      width: %(qrbox).3fmm; height: %(qrbox).3fmm; }
.qr svg { display: block; width: 100%%; height: 100%%; }
.linktext { font-size: 7pt; line-height: 1.5; }
.linktext .cmd { color: var(--green); }
.linktext .url { color: var(--dim); margin-top: .6mm; }
.linktext .hint { color: var(--dim); font-size: 5.6pt; margin-top: 1.2mm; }
.addr { margin-top: auto; font-size: 5.6pt; color: var(--dim); }
.addr > div { height: 2.75mm; line-height: 2.75mm; white-space: nowrap; }
.addr .kr { font-family: var(--kr); }
.addr .uni { color: var(--green); }
.addr .uni .kr { font-weight: 500; }

@media print {
  /* Chrome rounds the PDF page to ~92.12 x 51.90 mm. Paint the page itself in
     the card colour so that rounding slack is never a white sliver in the bleed. */
  html, body { background: var(--bg); }
  .face { margin: 0; break-after: page; }
  .face:last-child { break-after: auto; }
}
""" % {
        "fw": face_w, "fh": face_h, "pad": pad, "tk": SAFE - 1.2,
        "tx": (face_w - TRIM_W) / 2, "ty": (face_h - TRIM_H) / 2,
        "tw": TRIM_W, "th": TRIM_H,
        "quiet": quiet, "qrbox": QR_MM + 2 * quiet, **C,
    }

    front = """
<section class="face front" id="front"><div class="trim">
  <i class="tick tl"></i><i class="tick tr"></i><i class="tick bl"></i><i class="tick br"></i>
  <div class="safe">
    <div class="bar"><span class="logo">[<b>~</b>] NEURAL_SYSTEMS_LAB</span><span class="inst">HSMU</span></div>
    <div class="name">
      <div class="kr">%(name_kr)s</div>
      <div class="en">%(name_en)s<i class="cursor"></i></div>
    </div>
    <div class="meta">
      <div class="row"><span class="key">role :</span><span class="val">%(role_kr)s</span></div>
      <div class="row"><span class="key">dept :</span><span class="val">%(dept_kr)s</span></div>
      <div class="row"><span class="key"></span><span class="val sub">%(role_en)s</span></div>
    </div>
    <div class="contact">%(contact)s</div>
  </div>
</div></section>""" % {"name_kr": esc(k["name_kr"]), "name_en": esc(k["name_en"]),
                 "role_kr": esc(k["role_kr"]), "dept_kr": esc(k["dept_kr"]),
                 "role_en": esc(k["role_en"]), "contact": contact_html}

    back = """
<section class="face back" id="back"><div class="trim">
  <i class="tick tl"></i><i class="tick tr"></i><i class="tick bl"></i><i class="tick br"></i>
  <div class="safe">
    <div class="boot">
      <div class="g">NEURAL_SYSTEMS_LABORATORY :: BOOT SEQUENCE v4.2.1</div>
      <div class="a">ACCESS GRANTED :: Neural Systems Laboratory online</div>
    </div>
    <div class="link">
      <div class="qr" id="qr">%(qr)s</div>
      <div class="linktext">
        <div class="cmd">$ ./open_lab_page</div>
        <div class="url">%(url)s</div>
        <div class="hint">// scan to connect</div>
      </div>
    </div>
    <div class="addr">
      <div class="kr">%(postcode)s %(address_kr)s</div>
      %(address_en)s
      <div class="uni"><span class="kr">%(inst_kr)s</span> · %(inst_en)s</div>
    </div>
  </div>
</div></section>""" % {
        "qr": qr,
        "url": "<br>".join(esc(x) for x in k["url_lines"]),
        "postcode": esc(k["postcode"]), "address_kr": esc(k["address_kr"]),
        "address_en": "<div>%s</div>" % esc(", ".join(k["address_en"])),
        "inst_kr": esc(k["institution_kr"]), "inst_en": esc(k["institution_en"].upper()),
    }

    return ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>%s — business card</title>\n"
            '<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono'
            '&family=VT323&display=block" rel="stylesheet">\n'
            "<style>%s</style>\n</head>\n<body>%s%s\n</body>\n</html>\n"
            % (esc(k["name_en"]), css, front, back))


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def korean_font_file() -> str | None:
    pats = [r"C:\Windows\Fonts\NotoSansKR-Regular.*",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NotoSansKR-Regular.*"),
            r"C:\Windows\Fonts\NotoSansKR-VF.*",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\NotoSansKR-VF.*"),
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.*",
            "/Library/Fonts/NotoSansKR-Regular.*"]
    for pat in pats:
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


def check_glyphs(k: dict) -> list[str]:
    """Every non-ASCII character must exist in the Korean fallback font."""
    path = korean_font_file()
    if not path:
        return ["no Noto Sans KR / CJK font file found — cannot verify Hangul glyphs"]
    from fontTools.ttLib import TTFont, TTCollection
    font = TTCollection(path).fonts[0] if path.lower().endswith(".ttc") else TTFont(path)
    cmap = font.getBestCmap()
    text = " ".join(str(v) for v in k.values() if isinstance(v, str))
    text += " ".join(k["address_en"])
    missing = sorted({ch for ch in text if ord(ch) > 127 and ord(ch) not in cmap})
    return ["glyphs missing from %s: %s" % (os.path.basename(path), "".join(missing))] \
        if missing else []


SAFE_JS = """
(sel) => {
  // Measured from the trim box, not the page: the page edge moves with
  // Chrome's size rounding, the trim line does not.
  const mm = 96 / 25.4;
  const t = document.querySelector(sel + ' .trim').getBoundingClientRect();
  const lim = { l: t.left + %(in)f*mm, t: t.top + %(in)f*mm,
                r: t.right - %(in)f*mm, b: t.bottom - %(in)f*mm };
  const bad = [];
  const walk = document.createTreeWalker(document.querySelector(sel), NodeFilter.SHOW_TEXT);
  while (walk.nextNode()) {
    const n = walk.currentNode;
    if (!n.textContent.trim()) continue;
    const r = document.createRange(); r.selectNodeContents(n);
    const b = r.getBoundingClientRect();
    if (b.left < lim.l - .5 || b.right > lim.r + .5 || b.top < lim.t - .5 || b.bottom > lim.b + .5)
      bad.push(n.textContent.trim().slice(0, 40) + ' (' +
               [b.left - t.left, b.top - t.top, b.right - t.left, b.bottom - t.top]
               .map(v => (v / mm).toFixed(1)).join(', ') + ' mm from trim)');
  }
  const q = document.querySelector(sel + ' .qr');
  if (q) { const b = q.getBoundingClientRect();
    if (b.left < lim.l || b.right > lim.r || b.top < lim.t || b.bottom > lim.b) bad.push('QR panel'); }
  return bad;
}
""" % {"in": SAFE}


def probe_page_size(browser, w_mm: float, h_mm: float) -> tuple[float, float]:
    """The page size Chrome will really emit for a requested one."""
    import tempfile
    import fitz
    page = browser.new_page()
    page.set_content("<style>@page{size:%.3fmm %.3fmm;margin:0}</style>" % (w_mm, h_mm))
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "probe.pdf")
        page.pdf(path=path, width="%.3fmm" % w_mm, height="%.3fmm" % h_mm,
                 prefer_css_page_size=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        with fitz.open(path) as d:
            r = d[0].rect
            size = (r.width * 25.4 / 72, r.height * 25.4 / 72)
    page.close()
    return size


def check_pdf(path: str, name_kr: str) -> list[str]:
    """What a print shop's preflight would reject."""
    import fitz
    problems = []
    with fitz.open(path) as d:
        if len(d) != 2:
            problems.append("PDF has %d pages, expected 2 (front, back)" % len(d))
        for pg in d:
            r = pg.rect
            w, h = r.width * 25.4 / 72, r.height * 25.4 / 72
            bx, by = (w - TRIM_W) / 2, (h - TRIM_H) / 2
            if min(bx, by) < 0.9:
                problems.append("page %d bleed is %.2f / %.2f mm, need >= 0.9"
                                % (pg.number + 1, bx, by))
            pix = pg.get_pixmap(dpi=300)
            W, H = pix.width, pix.height
            edge = ([pix.pixel(x, 0) for x in range(W)] + [pix.pixel(x, H - 1) for x in range(W)]
                    + [pix.pixel(0, y) for y in range(H)] + [pix.pixel(W - 1, y) for y in range(H)])
            if max(max(p) for p in edge) > 40:
                problems.append("page %d has a light seam on its edge — the bleed is not "
                                "fully painted" % (pg.number + 1))
            for f in pg.get_fonts():
                if f[1] == "n/a":
                    problems.append("font %s is not embedded" % f[3])
        if name_kr and name_kr not in d[0].get_text():
            problems.append("front text is not selectable — fonts were rasterised")
    return problems


def _decode(img, url: str) -> bool:
    import cv2
    import numpy as np
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(np.array(img))
    return text == url


def check_qr(png_path: str, url: str) -> tuple[list[str], int | None]:
    """Decode the rendered card under the conditions it will actually meet.

    - 600 dpi, clean: the print master.
    - 300 dpi, blurred, JPEG q60: a phone photo — soft focus and compression.
    - 200 dpi, clean: a low-resolution capture at arm's length.

    Also returns the lowest dpi at which it still decodes, as a safety margin.
    A card held at ~20 cm in a 12 MP phone frame is well above 300 dpi, so
    that is the bar; OpenCV's own floor (~2.5 px per module) is not.
    """
    from PIL import Image, ImageFilter
    img = Image.open(png_path).convert("L")

    def at(dpi):
        s = dpi / DPI
        return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))),
                          Image.LANCZOS)

    problems = []
    if not _decode(img, url):
        problems.append("QR does not decode at 600 dpi")

    phone = at(300).filter(ImageFilter.GaussianBlur(1.0))
    buf = io.BytesIO()
    phone.save(buf, "JPEG", quality=60)
    buf.seek(0)
    if not _decode(Image.open(buf), url):
        problems.append("QR does not decode as a phone photo (300 dpi, blur, JPEG q60)")
    if not _decode(at(200), url):
        problems.append("QR does not decode at 200 dpi")

    floor = None
    for dpi in range(300, 90, -10):
        if _decode(at(dpi), url):
            floor = dpi
        else:
            break
    return problems, floor


# --------------------------------------------------------------------------

def render(d: dict, out_dir: str = OUT) -> list[str]:
    from playwright.sync_api import sync_playwright
    from PIL import Image

    os.makedirs(out_dir, exist_ok=True)
    k = card_data(d)
    qr, n_mod = qr_svg(k["url"])

    problems = check_glyphs(k)
    if not k["mobile"]:
        sys.stderr.write("  note: no mobile number — add person.phones.mobile to private.yaml\n")

    scale = DPI / 96.0
    html_path = os.path.join(out_dir, "card.html")
    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    made = [html_path]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=[
            "--font-render-hinting=none", "--force-color-profile=srgb"])

        # Size the face to the page Chrome will actually emit, so the bleed is
        # painted edge to edge. Asking again for that size must be stable.
        face_w, face_h = probe_page_size(browser, TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED)
        again = probe_page_size(browser, face_w, face_h)
        if abs(again[0] - face_w) > .01 or abs(again[1] - face_h) > .01:
            problems.append("Chrome page size is not stable: %.3f x %.3f then %.3f x %.3f"
                            % (face_w, face_h, again[0], again[1]))
        doc = build_html(k, qr, n_mod, face_w, face_h)
        io.open(html_path, "w", encoding="utf-8", newline="\n").write(doc)

        # -- PNG, at print resolution ------------------------------------
        page = browser.new_page(device_scale_factor=scale,
                                viewport={"width": 420, "height": 480})
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        for fam in ("Share Tech Mono", "VT323"):
            if not page.evaluate("document.fonts.check('12px \"%s\"')" % fam):
                problems.append("web font %r did not load — output would fall back" % fam)
        for sel in ("#front", "#back"):
            for b in page.evaluate(SAFE_JS, sel):
                problems.append("%s: text inside the %.0f mm safety margin: %s"
                                % (sel[1:], SAFE, b))

        # Screenshot the whole face, then crop the trim box at its exact
        # device-pixel position. (An element screenshot of the trim box rounds
        # its clip outward to whole CSS pixels and picks up ~0.3 mm of bleed.)
        for face in ("front", "back"):
            box = page.evaluate(
                "(s) => { const f = document.querySelector(s).getBoundingClientRect(),"
                " t = document.querySelector(s + ' .trim').getBoundingClientRect();"
                " return [t.left - f.left, t.top - f.top, t.width, t.height]; }", "#" + face)
            raw = os.path.join(out_dir, "_%s-face.png" % face)
            page.locator("#" + face).screenshot(path=raw)
            x, y, w, h = (round(v * scale) for v in box)
            out = os.path.join(out_dir, "card-%s.png" % face)
            with Image.open(raw) as im:
                im.crop((x, y, x + w, y + h)).save(out, dpi=(DPI, DPI))
            os.remove(raw)
            made.append(out)
        page.close()

        # -- PDF, vector, with bleed -------------------------------------
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.evaluate("document.fonts.ready")
        page.emulate_media(media="print")
        pdf = os.path.join(out_dir, "card-print.pdf")
        page.pdf(path=pdf, width="%.3fmm" % face_w, height="%.3fmm" % face_h,
                 print_background=True, prefer_css_page_size=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        made.append(pdf)
        browser.close()

    problems += check_pdf(pdf, k["name_kr"])
    print("  page %.3f x %.3f mm · bleed %.2f / %.2f mm"
          % (face_w, face_h, (face_w - TRIM_W) / 2, (face_h - TRIM_H) / 2))

    qr_problems, qr_floor = check_qr(os.path.join(out_dir, "card-back.png"), k["url"])
    problems += qr_problems
    if qr_floor:
        print("  QR decodes down to %d dpi (%.1f px per module)"
              % (qr_floor, qr_floor / 25.4 * QR_MM / n_mod))

    # -- side-by-side preview ----------------------------------------------
    f = Image.open(os.path.join(out_dir, "card-front.png")).convert("RGB")
    b = Image.open(os.path.join(out_dir, "card-back.png")).convert("RGB")
    gap = int(f.width * 0.06)
    prev = Image.new("RGB", (f.width + b.width + 3 * gap, f.height + 2 * gap), (58, 63, 58))
    prev.paste(f, (gap, gap))
    prev.paste(b, (2 * gap + f.width, gap))
    prev = prev.resize((prev.width // 3, prev.height // 3), Image.LANCZOS)
    preview = os.path.join(out_dir, "card-preview.png")
    prev.save(preview)
    made.append(preview)

    if problems:
        raise RuntimeError("card checks failed:\n  - " + "\n  - ".join(problems))
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the business card")
    ap.add_argument("--out", default=OUT, help="output directory (default build-private/card)")
    args = ap.parse_args()
    d = cvdata.load()                       # private.yaml supplies the mobile
    try:
        made = render(d, args.out)
    except RuntimeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    print("card: all checks passed")
    for m in made:
        print("  %-18s %7.1f KB" % (os.path.basename(m), os.path.getsize(m) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
