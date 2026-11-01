"""Step 2 – Vectorise the manual map (Mentahan/Pemetaan.png) into geocoded data.

Pipeline
  Pemetaan.png pixel  --(red-boundary bbox fit)-->  screenshot pixel
  screenshot pixel    --(georef.json, SIFT fit)-->   WebMercator pixel (z18)
  WebMercator pixel   -->  WGS84 lng/lat  -->  local ENU metres (x = east, z = south)

Outputs
  public/data/campus.json      geometry consumed by the Three.js app (local metres)
  public/data/campus.geojson   the same features in WGS84 (real geocoding / GIS interop)
  public/textures/satellite.jpg  Esri World Imagery orthophoto covering the campus
"""
import json, math, os, random
import numpy as np, cv2
from PIL import Image
from georef import fetch, lnglat_to_px

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "out")
PUB = os.path.join(ROOT, "public")
os.makedirs(os.path.join(PUB, "data"), exist_ok=True)
os.makedirs(os.path.join(PUB, "textures"), exist_ok=True)

G = json.load(open(os.path.join(OUT, "georef.json")))
H = np.array(G["H"]); ZG = G["zoom"]

ORIGIN = (5.399226, 95.435794)  # lat, lng of the pesantren (from PRD)

def merc_to_lnglat(x, y, z):
    s = 256 * 2 ** z
    lng = x / s * 360 - 180
    n = math.pi - 2 * math.pi * y / s
    return lng, math.degrees(math.atan(math.sinh(n)))

M_PER_DEG_LAT = 110574.0
M_PER_DEG_LNG = 111320.0 * math.cos(math.radians(ORIGIN[0]))

def lnglat_to_local(lng, lat):
    return ((lng - ORIGIN[1]) * M_PER_DEG_LNG, -(lat - ORIGIN[0]) * M_PER_DEG_LAT)

def local_to_lnglat(x, z):
    return (ORIGIN[1] + x / M_PER_DEG_LNG, ORIGIN[0] - z / M_PER_DEG_LAT)

def shot_to_lnglat(px, py):
    v = H @ np.array([px, py, 1.0]); v /= v[2]
    return merc_to_lnglat(v[0], v[1], ZG)

# ---------------------------------------------------------------- load images
clean = np.array(Image.open(os.path.join(ROOT, "Mentahan", "Pemetaan.png")).convert("RGBA"))
shot = np.array(Image.open(os.path.join(ROOT, "Mentahan", "Pemetaan Maps Tanpa penomoran.png")).convert("RGB"))
rgb, alpha = clean[..., :3].astype(int), clean[..., 3]

def cmask(img, col, tol=40):
    return (np.abs(img.astype(int) - np.array(col)).sum(2) < tol)

RED, GREY, YEL, GRN, BRN, ROADG, CYAN = (255, 0, 0), (217, 217, 217), (255, 242, 0), (76, 175, 80), (121, 113, 93), (156, 154, 154), (0, 212, 255)
opaque = alpha > 128

# fit clean -> screenshot with the red boundary line (scale + translation per axis)
def bbox(m):
    ys, xs = np.nonzero(m); return xs.min(), ys.min(), xs.max(), ys.max()
cb = bbox(cmask(rgb, RED) & opaque)
sb = bbox(cmask(shot, RED, 30))
sx = (sb[2] - sb[0]) / (cb[2] - cb[0]); sy = (sb[3] - sb[1]) / (cb[3] - cb[1])
print("clean->shot scale", sx, sy)

def clean_to_local(px, py):
    return lnglat_to_local(*shot_to_lnglat(sb[0] + (px - cb[0]) * sx, sb[1] + (py - cb[1]) * sy))

def contour_local(c):
    return [list(map(lambda v: round(v, 2), clean_to_local(float(p[0][0]), float(p[0][1])))) for p in c]

def polys_from_mask(m, min_area=60, eps=1.6, holes=False, rectify=False):
    m = m.astype(np.uint8) * 255
    mode = cv2.RETR_CCOMP if holes else cv2.RETR_EXTERNAL
    cs, hier = cv2.findContours(m, mode, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    if hier is None: return out
    hier = hier[0]
    for i, c in enumerate(cs):
        if hier[i][3] != -1: continue  # hole – handled by parent
        if cv2.contourArea(c) < min_area: continue
        if rectify:
            rect = cv2.minAreaRect(c)
            if cv2.contourArea(c) / max(1, rect[1][0] * rect[1][1]) > 0.88:
                c = cv2.boxPoints(rect).reshape(-1, 1, 2)
            else:
                c = cv2.approxPolyDP(c, 3.2, True)
        else:
            c = cv2.approxPolyDP(c, eps, True)
        item = {"outer": contour_local(c), "holes": []}
        if holes:
            j = hier[i][2]
            while j != -1:
                if cv2.contourArea(cs[j]) > 30:
                    item["holes"].append(contour_local(cv2.approxPolyDP(cs[j], eps, True)))
                j = hier[j][0]
        out.append(item)
    return out

def clean_mask(m, k=3):
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((k, k), np.uint8)) > 0

# ------------------------------------------------------------------ features
red = cmask(rgb, RED, 120) & opaque
# boundary = largest filled region bounded by the red line
fill = cv2.morphologyEx(red.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
cs, _ = cv2.findContours(fill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
outer = max(cs, key=cv2.contourArea)
boundary = contour_local(cv2.approxPolyDP(outer, 1.2, True))

grey = clean_mask(cmask(rgb, GREY, 30) & opaque, 3)
yellow = clean_mask((cmask(rgb, YEL, 90)) & opaque, 3)
green = clean_mask(cmask(rgb, GRN, 40) & opaque, 3)
# buildings never overlap sports fields: carve fields out and drop thin slivers
grey = grey & ~(cv2.dilate(green.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
grey = cv2.morphologyEx(grey.astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8)) > 0
brown = clean_mask(cmask(rgb, BRN, 40) & opaque, 3)
cyan = clean_mask(cmask(rgb, CYAN, 60) & opaque, 3)
asphalt = clean_mask(((rgb.sum(2) < 60) | cmask(rgb, ROADG, 30)) & opaque, 3)
asphalt_core = clean_mask((rgb.sum(2) < 90) & opaque, 3)

# keep only the asphalt line along the boundary (drop isolated specks)
roads_main = polys_from_mask(asphalt, 400, 1.5, holes=True)
roads_core = polys_from_mask(asphalt_core, 200, 1.2, holes=True)
roads_internal = polys_from_mask(yellow, 80, 1.5, holes=True)
rivers = polys_from_mask(brown, 300, 1.5)
fields = polys_from_mask(green, 80, 1.5)
globe = polys_from_mask(cyan, 20, 1.5)
building_polys = polys_from_mask(grey, 120, 2.2, rectify=True)
fields = polys_from_mask(green, 80, 1.5, rectify=True)

# --------------------------------------------------------------- locations
# numbered markers detected as the difference between the two screenshots
MARKERS = {1: (988, 127), 2: (1044, 175), 3: (1135, 246), 4: (952, 320), 5: (1296, 533), 6: (812, 482),
           7: (1301, 654), 8: (1218, 677), 9: (770, 685), 10: (1428, 755), 11: (1316, 760), 12: (1204, 774),
           13: (1151, 866), 14: (1290, 896), 15: (1463, 893), 16: (1246, 1009), 17: (1154, 972), 18: (1062, 1105),
           19: (1285, 1182), 20: (1043, 1276), 21: (917, 1182), 22: (836, 1113), 23: (818, 962), 24: (884, 533),
           25: (699, 690), 26: (1031, 357)}
LOC_META = json.load(open(os.path.join(ROOT, "tools", "locations.json"), encoding="utf-8"))
locations = []
for lid, (px, py) in MARKERS.items():
    lng, lat = shot_to_lnglat(px, py)
    x, z = lnglat_to_local(lng, lat)
    meta = LOC_META[str(lid)]
    locations.append({"id": lid, **meta, "lat": round(lat, 7), "lng": round(lng, 7), "x": round(x, 2), "z": round(z, 2)})

def pip(pt, poly):
    x, y = pt; inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside

def centroid(poly):
    a = np.array(poly); return a.mean(0)

def assign(polys, kinds):
    for p in polys:
        c = centroid(p["outer"])
        cand = [l for l in locations if l["kind"] in kinds]
        inside = [l for l in cand if pip((l["x"], l["z"]), p["outer"])]
        if inside:
            p["loc"] = inside[0]["id"]
        else:
            d = sorted(cand, key=lambda l: (l["x"] - c[0]) ** 2 + (l["z"] - c[1]) ** 2)
            dist = math.hypot(d[0]["x"] - c[0], d[0]["z"] - c[1])
            p["loc"] = d[0]["id"] if dist < 45 else None
        p["centroid"] = [round(float(c[0]), 2), round(float(c[1]), 2)]

assign(building_polys, {"building"})
assign(fields, {"field"})

# ---------------------------------------------------------------- satellite
xs = [p[0] for p in boundary]; zs = [p[1] for p in boundary]
MARGIN = 160
bx0, bx1, bz0, bz1 = min(xs) - MARGIN, max(xs) + MARGIN, min(zs) - MARGIN, max(zs) + MARGIN
ZS = 18  # z19 returns grey "no data" placeholder tiles for this area
lng0, lat0 = local_to_lnglat(bx0, bz0); lng1, lat1 = local_to_lnglat(bx1, bz1)
gx0, gy0 = lnglat_to_px(lng0, lat0, ZS); gx1, gy1 = lnglat_to_px(lng1, lat1, ZS)
tx0, ty0, tx1, ty1 = int(gx0 // 256), int(gy0 // 256), int(gx1 // 256), int(gy1 // 256)
mos = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        try:
            mos.paste(fetch(ZS, tx, ty), ((tx - tx0) * 256, (ty - ty0) * 256))
        except Exception as e:
            print("tile fail", tx, ty, e)
crop = mos.crop((int(gx0 - tx0 * 256), int(gy0 - ty0 * 256), int(gx1 - tx0 * 256), int(gy1 - ty0 * 256)))
W = 3072
scale = W / max(crop.size)
crop_s = crop.resize((int(crop.size[0] * scale), int(crop.size[1] * scale)), Image.LANCZOS)
crop_s.save(os.path.join(PUB, "textures", "satellite.jpg"), quality=86)
satellite = {"url": "textures/satellite.jpg", "x0": round(bx0, 2), "x1": round(bx1, 2), "z0": round(bz0, 2), "z1": round(bz1, 2),
             "attribution": "Imagery © Esri, Maxar, Earthstar Geographics"}
print("satellite", crop_s.size)

# ------------------------------------------------------------------- trees
# sample tree positions from real vegetation in the orthophoto
sat = np.array(crop).astype(np.float32)
R, Gc, B = sat[..., 0], sat[..., 1], sat[..., 2]
exg = (2 * Gc - R - B)
gray = cv2.cvtColor(sat.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
tex = np.sqrt(np.maximum(cv2.blur(gray * gray, (9, 9)) - cv2.blur(gray, (9, 9)) ** 2, 0))
# tree canopy = dark, green-ish and textured; lawns/grass are bright & smooth, bare soil is brown
veg = (exg > 4) & (gray < 108) & (tex > 4.5)
veg = cv2.morphologyEx(veg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
mpp_x = (bx1 - bx0) / crop.size[0]; mpp_z = (bz1 - bz0) / crop.size[1]

# rasterise "no tree" zones in local metres (1 m grid)
gw, gh = int(bx1 - bx0) + 1, int(bz1 - bz0) + 1
block = np.zeros((gh, gw), np.uint8)
inside = np.zeros((gh, gw), np.uint8)
def to_grid(poly): return np.array([[(p[0] - bx0), (p[1] - bz0)] for p in poly], np.int32)
cv2.fillPoly(inside, [to_grid(boundary)], 1)
inside = cv2.erode(inside, np.ones((9, 9), np.uint8))
for group, pad in ((building_polys, 5), (fields, 3), (rivers, 3), (globe, 6)):
    for p in group:
        cv2.fillPoly(block, [to_grid(p["outer"])], 1)
road_m = np.zeros_like(block)
for group in (roads_main, roads_internal):
    for p in group:
        cv2.fillPoly(road_m, [to_grid(p["outer"])], 1)
        for h in p["holes"]: cv2.fillPoly(road_m, [to_grid(h)], 0)
block = cv2.dilate(block | road_m, np.ones((7, 7), np.uint8))
allowed = (inside > 0) & (block == 0)

rng = random.Random(7)
# --- vegetation density classes from the orthophoto (1 m grid) ---
veg_m = cv2.resize(veg.astype(np.float32), (gw, gh), interpolation=cv2.INTER_AREA)
canopy = cv2.GaussianBlur(veg_m, (0, 0), 7)          # canopy cover in a ~15 m neighbourhood
FOREST, SPARSE = 0.50, 0.22
cls = np.where(canopy >= FOREST, 2, np.where(canopy >= SPARSE, 1, 0)).astype(np.uint8)
cls[inside == 0] = 0

trees = []
taken = np.zeros_like(block)
cand = [tuple(c) for c in np.argwhere(allowed)]
rng.shuffle(cand)
SPACING = {2: (3, 4, 4, 5), 1: (5, 6, 7), 0: (7, 8)}
KEEP = {2: 0.95, 1: 0.30, 0: 0.025}
for (gz, gx) in cand:
    if taken[gz, gx]: continue
    c = int(cls[gz, gx])
    local = veg_m[max(0, gz - 2):gz + 3, max(0, gx - 2):gx + 3].mean()
    p = KEEP[c] * (0.55 + 0.45 * min(1.0, local * 1.6))
    if rng.random() > p: continue
    r = rng.choice(SPACING[c])
    cv2.circle(taken, (gx, gz), r, 1, -1)
    x, z = gx + bx0, gz + bz0
    if c == 2:   # forest: broad canopy trees, few palms
        kind = 1 if rng.random() < 0.08 else (2 if rng.random() < 0.08 else 0)
        scale = 1.0 + rng.random() * 0.6
    else:        # yards / open land: palms and ornamental trees
        kind = 1 if rng.random() < 0.32 else (2 if rng.random() < 0.15 else 0)
        scale = 0.8 + rng.random() * 0.45
    trees.append([round(x, 1), round(z, 1), kind, round(scale, 2), c])
print("trees", len(trees), "forest", sum(t[4] == 2 for t in trees), "sparse", sum(t[4] == 1 for t in trees), "open", sum(t[4] == 0 for t in trees))

# forest areas as polygons (for a subtle ground tint under the canopy)
forest_mask = ((cls == 2).astype(np.uint8) * 255)
forest_mask = cv2.morphologyEx(forest_mask, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
forest_polys = []
fcs, fh = cv2.findContours(forest_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
if fh is not None:
    for i, c in enumerate(fcs):
        if fh[0][i][3] != -1 or cv2.contourArea(c) < 250: continue
        c = cv2.approxPolyDP(c, 2.0, True)
        holes = []
        j = fh[0][i][2]
        while j != -1:
            if cv2.contourArea(fcs[j]) > 120:
                holes.append([[round(float(p[0][0] + bx0), 1), round(float(p[0][1] + bz0), 1)] for p in cv2.approxPolyDP(fcs[j], 2.0, True)])
            j = fh[0][j][0]
        forest_polys.append({"outer": [[round(float(p[0][0] + bx0), 1), round(float(p[0][1] + bz0), 1)] for p in c], "holes": holes})
cv2.imwrite(os.path.join(OUT, "vegetation_classes.png"), (np.stack([cls == 0, cls == 1, cls == 2], -1) * np.array([200, 140, 60])).astype(np.uint8))

data = {
    "name": "Pesantren Tgk. Chiek Oemar Diyan",
    "address": "9CXP+H7 Krueng Lamkareung, Kabupaten Aceh Besar, Aceh",
    "origin": {"lat": ORIGIN[0], "lng": ORIGIN[1]},
    "boundary": boundary,
    "roadsMain": roads_main, "roadsCore": roads_core, "roadsInternal": roads_internal, "rivers": rivers,
    "fields": fields, "globe": globe, "buildings": building_polys,
    "locations": locations, "trees": trees, "forest": forest_polys, "satellite": satellite,
}
json.dump(data, open(os.path.join(PUB, "data", "campus.json"), "w"), separators=(",", ":"))

# --------------------------------------------------------------- GeoJSON export
def ring_ll(ring):
    r = [list(map(lambda v: round(v, 7), local_to_lnglat(*p))) for p in ring]
    return r + [r[0]]
feats = [{"type": "Feature", "properties": {"type": "boundary"}, "geometry": {"type": "Polygon", "coordinates": [ring_ll(boundary)]}}]
for t, group in (("road_main", roads_main), ("road_internal", roads_internal), ("river", rivers), ("field", fields), ("building", building_polys), ("globe", globe)):
    for p in group:
        props = {"type": t}
        if p.get("loc"): props["location_id"] = p["loc"]
        feats.append({"type": "Feature", "properties": props, "geometry": {"type": "Polygon", "coordinates": [ring_ll(p["outer"])] + [ring_ll(h) for h in p["holes"]]}})
for l in locations:
    feats.append({"type": "Feature", "properties": {"type": "location", "id": l["id"], "name": l["name"], "category": l["category"]},
                  "geometry": {"type": "Point", "coordinates": [l["lng"], l["lat"]]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(PUB, "data", "campus.geojson"), "w"))

# debug preview
dbg = np.full((gh, gw, 3), 245, np.uint8)
cv2.fillPoly(dbg, [to_grid(boundary)], (255, 255, 255))
for p in fields: cv2.fillPoly(dbg, [to_grid(p["outer"])], (80, 175, 76))
for p in rivers: cv2.fillPoly(dbg, [to_grid(p["outer"])], (93, 113, 121))
for p in roads_internal + roads_main:
    cv2.fillPoly(dbg, [to_grid(p["outer"])], (0, 220, 255) if p in roads_internal else (30, 30, 30))
    for h in p["holes"]: cv2.fillPoly(dbg, [to_grid(h)], (255, 255, 255))
for p in building_polys: cv2.fillPoly(dbg, [to_grid(p["outer"])], (190, 190, 190))
for p in fields: cv2.fillPoly(dbg, [to_grid(p["outer"])], (80, 175, 76))
for t in trees: cv2.circle(dbg, (int(t[0] - bx0), int(t[1] - bz0)), 2, ((120, 200, 120), (60, 150, 60), (20, 90, 20))[t[4]], -1)

# vector overlay on the orthophoto (alignment check)
ov = cv2.cvtColor(np.array(crop.resize((gw, gh))), cv2.COLOR_RGB2BGR)
for p in roads_internal: cv2.polylines(ov, [to_grid(p["outer"])] + [to_grid(h) for h in p["holes"]], True, (0, 230, 255), 1)
for p in building_polys: cv2.polylines(ov, [to_grid(p["outer"])], True, (255, 255, 255), 1)
for p in fields: cv2.polylines(ov, [to_grid(p["outer"])], True, (0, 255, 0), 1)
cv2.polylines(ov, [to_grid(boundary)], True, (0, 0, 255), 1)
cv2.imwrite(os.path.join(OUT, "overlay_check.png"), ov)
for l in locations: cv2.putText(dbg, str(l["id"]), (int(l["x"] - bx0), int(l["z"] - bz0)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
cv2.polylines(dbg, [to_grid(boundary)], True, (0, 0, 255), 1)
cv2.imwrite(os.path.join(OUT, "extract_debug.png"), dbg)
print("buildings", len(building_polys), "fields", len(fields), "roads", len(roads_internal), len(roads_main), "rivers", len(rivers))
