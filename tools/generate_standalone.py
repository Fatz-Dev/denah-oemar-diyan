"""Generate standalone zero-dependency HTML files:
1. denah_3d_offline.html (Interactive 3D Map)
2. spanduk_mading_offline.html (Spanduk & Mading Poster Board)
"""
import base64, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
PUB = os.path.join(ROOT, "public")
TEX = os.path.join(PUB, "textures")

def to_b64_uri(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    raw = open(filepath, "rb").read()
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")

# ---------------------------------------------------------------------------
# 1. Generate denah_3d_offline.html
# ---------------------------------------------------------------------------
campus_json = json.load(open(os.path.join(PUB, "data", "campus.json"), encoding="utf-8"))
sat_b64 = to_b64_uri(os.path.join(TEX, "satellite.jpg"))
campus_json["satellite"]["url"] = sat_b64

css_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".css") and f.startswith("main")]
if not css_files:
    css_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".css") and "spanduk" not in f]
css_content = open(os.path.join(DIST, "assets", css_files[0]), encoding="utf-8").read()

js_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".js") and f.startswith("main")]
if not js_files:
    js_files = [f for f in os.listdir(os.path.join(DIST, "assets")) if f.endswith(".js") and "spanduk" not in f]
js_content = open(os.path.join(DIST, "assets", js_files[0]), encoding="utf-8").read()

campus_inlined_code = f"window.__CAMPUS_DATA__ = {json.dumps(campus_json, separators=(',', ':'))};"

html_content = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
html_content = html_content.replace('href="/spanduk-mading"', 'href="spanduk_mading_offline.html"')
html_content = html_content.replace("</head>", f"<style>\n{css_content}\n</style>\n</head>")
script_tag = '<script type="module" src="/src/main.js"></script>'
inlined_script = f"<script type=\"module\">\n{campus_inlined_code}\n{js_content}\n</script>"
html_content = html_content.replace(script_tag, inlined_script)

out_3d = os.path.join(ROOT, "denah_3d_offline.html")
open(out_3d, "w", encoding="utf-8").write(html_content)
print(f"Generated standalone 3D map: {out_3d} ({os.path.getsize(out_3d):,} bytes)")

# ---------------------------------------------------------------------------
# 2. Generate spanduk_mading_offline.html & spanduk_mading_v2_offline.html
# ---------------------------------------------------------------------------
markers_json = json.load(open(os.path.join(PUB, "data", "mading_markers.json"), encoding="utf-8"))
spanduk_css = open(os.path.join(ROOT, "src", "spanduk.css"), encoding="utf-8").read()
spanduk_js = open(os.path.join(ROOT, "src", "spanduk.js"), encoding="utf-8").read()
spanduk_js = spanduk_js.replace("import './spanduk.css';", "")

hdr_b64 = to_b64_uri(os.path.join(TEX, "mading_header_bg.jpg"))
spanduk_css = spanduk_css.replace("url('/textures/mading_header_bg.jpg')", f"url('{hdr_b64}')")

ilus_2d_b64 = to_b64_uri(os.path.join(TEX, "mading_ilustrasi.jpg"))
sat_2d_b64 = to_b64_uri(os.path.join(TEX, "mading_satelit.jpg"))
ilus_3d_b64 = to_b64_uri(os.path.join(TEX, "render_3d_ilustrasi.png"))
sat_3d_b64 = to_b64_uri(os.path.join(TEX, "render_3d_satelit.png"))
logo_od_b64 = to_b64_uri(os.path.join(PUB, "image", "logo-od.png"))
qr_code_b64 = to_b64_uri(os.path.join(PUB, "image", "qr-code.png"))

spanduk_globals = (
    f"window.__MADING_MARKERS__ = {json.dumps(markers_json, ensure_ascii=False, separators=(',', ':'))};\n"
    f"window.__IMG_2D_ILUS__ = '{ilus_2d_b64}';\n"
    f"window.__IMG_2D_SAT__ = '{sat_2d_b64}';\n"
    f"window.__IMG_3D_ILUS__ = '{ilus_3d_b64}';\n"
    f"window.__IMG_3D_SAT__ = '{sat_3d_b64}';\n"
)

def build_spanduk_offline(folder_name, out_filename):
    spanduk_html = open(os.path.join(ROOT, folder_name, "index.html"), encoding="utf-8").read()
    spanduk_html = spanduk_html.replace('href="/"', 'href="denah_3d_offline.html"')
    spanduk_html = spanduk_html.replace('href="/spanduk-mading"', 'href="spanduk_mading_offline.html"')
    spanduk_html = spanduk_html.replace('href="/spanduk-mading-v2"', 'href="spanduk_mading_v2_offline.html"')
    spanduk_html = spanduk_html.replace('/image/logo-od.png', logo_od_b64)
    spanduk_html = spanduk_html.replace('../image/logo-od.png', logo_od_b64)
    spanduk_html = spanduk_html.replace('/image/qr-code.png', qr_code_b64)
    spanduk_html = spanduk_html.replace('../image/qr-code.png', qr_code_b64)

    for img_name in ["mading_logo.png", "logo-uin.png", "logo-ppkpm.png", "mading_ilustrasi.jpg", "mading_satelit.jpg"] + [f"gedung_{i}.jpg" for i in range(1, 9)]:
        b64 = to_b64_uri(os.path.join(TEX, img_name))
        spanduk_html = spanduk_html.replace(f"/textures/{img_name}?v=2", b64)
        spanduk_html = spanduk_html.replace(f"/textures/{img_name}", b64)

    spanduk_html = spanduk_html.replace("</head>", f"<style>\n{spanduk_css}\n</style>\n</head>")
    spanduk_html = spanduk_html.replace(
        '<script type="module" src="/src/spanduk.js"></script>',
        f"<script type=\"module\">\n{spanduk_globals}\n{spanduk_js}\n</script>",
    )

    out_path = os.path.join(ROOT, out_filename)
    open(out_path, "w", encoding="utf-8").write(spanduk_html)
    print(f"Generated standalone Spanduk ({folder_name}): {out_path} ({os.path.getsize(out_path):,} bytes)")

build_spanduk_offline("spanduk-mading", "spanduk_mading_offline.html")
build_spanduk_offline("spanduk-mading-v2", "spanduk_mading_v2_offline.html")
