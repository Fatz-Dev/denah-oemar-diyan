"""Step 1 – Georeference the annotated Google screenshot against Esri World Imagery.

Downloads an Esri tile mosaic around the pesantren, matches SIFT features against
`Mentahan/Pemetaan Maps Tanpa penomoran.png` and stores a homography that maps
screenshot pixels -> global WebMercator pixel coords at zoom Z.
"""
import json, math, os, io, urllib.request
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "out")
os.makedirs(OUT, exist_ok=True)

LAT, LNG = 5.399226, 95.435794
Z = 18
N = 8  # tiles per side

def lnglat_to_px(lng, lat, z):
    s = 256 * 2 ** z
    x = (lng + 180) / 360 * s
    siny = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * s
    return x, y

def fetch(z, x, y):
    cache = os.path.join(OUT, "tiles", f"{z}_{x}_{y}.jpg")
    if os.path.exists(cache):
        return Image.open(cache).convert("RGB")
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "denah-georef"}), timeout=30).read()
    open(cache, "wb").write(data)
    return Image.open(io.BytesIO(data)).convert("RGB")

def mosaic(z, n):
    cx, cy = lnglat_to_px(LNG, LAT, z)
    tx0, ty0 = int(cx // 256) - n // 2, int(cy // 256) - n // 2
    img = Image.new("RGB", (256 * n, 256 * n))
    for i in range(n):
        for j in range(n):
            img.paste(fetch(z, tx0 + i, ty0 + j), (i * 256, j * 256))
    return img, tx0 * 256, ty0 * 256

if __name__ == "__main__":
    esri, ox, oy = mosaic(Z, N)
    esri.save(os.path.join(OUT, "esri_mosaic.jpg"))
    shot = cv2.imread(os.path.join(ROOT, "Mentahan", "Pemetaan Maps Tanpa penomoran.png"))
    E = cv2.cvtColor(np.array(esri), cv2.COLOR_RGB2BGR)

    # mask out flat overlay colours in the screenshot so only imagery is matched
    hsv = cv2.cvtColor(shot, cv2.COLOR_BGR2HSV)
    overlay = (hsv[..., 1] > 200) | ((np.abs(shot.astype(int) - 217).sum(2) < 12))
    mask = (~overlay).astype(np.uint8) * 255
    mask = cv2.erode(mask, np.ones((9, 9), np.uint8))

    sift = cv2.SIFT_create(nfeatures=15000)
    g1 = cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(E, cv2.COLOR_BGR2GRAY)
    k2, d2 = sift.detectAndCompute(g2, None)
    best = None
    for scale in (0.35, 0.45, 0.55, 0.65, 0.8, 1.0):  # screenshot downscaled towards esri resolution
        g1s = cv2.resize(g1, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        ms = cv2.resize(mask, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        k1, d1 = sift.detectAndCompute(g1s, ms)
        m = cv2.BFMatcher().knnMatch(d1, d2, k=2)
        good = [a for a, b in m if a.distance < 0.8 * b.distance]
        if len(good) < 10:
            continue
        p1 = np.float32([k1[a.queryIdx].pt for a in good]) / scale
        p2 = np.float32([k2[a.trainIdx].pt for a in good])
        A, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=4.0, maxIters=20000)
        n_in = int(inl.sum()) if inl is not None else 0
        print(f"scale {scale}: good={len(good)} inliers={n_in} A={None if A is None else A.round(4).tolist()}")
        if A is not None and (best is None or n_in > best[1]):
            best = (np.vstack([A, [0, 0, 1]]), n_in)
    H, n_in = best
    # shift to global webmercator pixel coords at zoom Z
    T = np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]], float)
    Hg = T @ H
    json.dump({"zoom": Z, "H": Hg.tolist(), "inliers": n_in}, open(os.path.join(OUT, "georef.json"), "w"), indent=1)

    # diagnostics: warp the screenshot onto esri for visual check
    warped = cv2.warpPerspective(shot, H, (E.shape[1], E.shape[0]))
    blend = cv2.addWeighted(E, 0.5, warped, 0.5, 0)
    cv2.imwrite(os.path.join(OUT, "georef_check.jpg"), blend)
    s = Hg @ np.array([1002, 1002, 1.0]); s /= s[2]
    def px_to_lnglat(x, y, z):
        sz = 256 * 2 ** z
        lng = x / sz * 360 - 180
        n = math.pi - 2 * math.pi * y / sz
        return lng, math.degrees(math.atan(math.sinh(n)))
    print("screenshot centre ->", px_to_lnglat(s[0], s[1], Z))
