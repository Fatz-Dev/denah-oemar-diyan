"""Generate high-resolution visual assets for /spanduk-mading page:
1. public/textures/mading_logo.png (Pesantren Modern Tgk. Chiek Oemar Diyan emblem)
2. public/textures/gedung_1.jpg .. gedung_8.jpg (8 main building photos from Example-Desain.jpeg)
3. public/textures/mading_ilustrasi.jpg (High-res 2.5D illustrated map of actual Pesantren Oemar Diyan campus)
4. public/textures/mading_satelit.jpg (High-res satellite map of actual Pesantren Oemar Diyan campus with roof overlays)
5. public/data/mading_markers.json (Normalized coordinates & metadata for all 26 numbered locations)
"""
import json, math, os, random
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "public")
TEX = os.path.join(PUB, "textures")
os.makedirs(TEX, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Render High-Resolution 800x800 Logo & Extract 8 Building Photos
# ---------------------------------------------------------------------------
ex_path = os.path.join(ROOT, "Mentahan", "Example-Desain.jpeg")
ex_im = Image.open(ex_path).convert("RGB")

def generate_crisp_logo(out_path):
    SS = 2
    OUT = 800
    W = OUT * SS
    C = W / 2.0
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def p(x, y):
        return (int(round(x * SS)), int(round(y * SS)))

    def pts(seq):
        return [p(x, y) for x, y in seq]

    draw.ellipse([p(400 - 392, 400 - 392), p(400 + 392, 400 + 392)], fill=(255, 255, 255, 255))
    draw.ellipse([p(400 - 382, 400 - 382), p(400 + 382, 400 + 382)], outline=(13, 118, 56, 255), width=11 * SS)
    draw.ellipse([p(400 - 365, 400 - 365), p(400 + 365, 400 + 365)], outline=(9, 72, 35, 255), width=5 * SS)

    inner = Image.new("RGBA", (W, W), (255, 255, 255, 255))
    idraw = ImageDraw.Draw(inner)
    for y in range(130 * SS, 450 * SS):
        t = (y - 130 * SS) / (320.0 * SS)
        idraw.line([(130 * SS, y), (670 * SS, y)], fill=(int(255 - 4 * t), int(255 - 1 * t), int(255 - 3 * t), 255))

    idraw.ellipse([p(120, 412), p(285, 575)], fill=(7, 162, 54, 255), outline=(5, 125, 40, 255), width=2 * SS)
    idraw.ellipse([p(515, 412), p(680, 575)], fill=(6, 152, 50, 255), outline=(5, 118, 38, 255), width=2 * SS)
    idraw.ellipse([p(135, 422), p(255, 520)], fill=(18, 178, 66, 255))
    idraw.ellipse([p(545, 422), p(665, 520)], fill=(14, 168, 60, 255))

    for y in range(510 * SS, 670 * SS):
        t = (y - 510 * SS) / (160.0 * SS)
        idraw.line([(130 * SS, y), (670 * SS, y)], fill=(int(8 * (1 - t) + 4 * t), int(164 * (1 - t) + 118 * t), int(52 * (1 - t) + 36 * t), 255))

    idraw.polygon(pts([(195, 536), (400, 512), (605, 536), (545, 588), (255, 588)]), fill=(4, 102, 32, 255))
    idraw.line(pts([(400, 568), (400, 650)]), fill=(68, 202, 102, 255), width=3 * SS)

    idraw.polygon(pts([(212, 376), (256, 368), (256, 520), (212, 526)]), fill=(244, 247, 245, 255), outline=(28, 52, 36, 255), width=3 * SS)
    idraw.polygon(pts([(544, 368), (588, 376), (588, 526), (544, 520)]), fill=(192, 204, 194, 255), outline=(28, 52, 36, 255), width=3 * SS)
    idraw.line(pts([(208, 376), (256, 368)]), fill=(20, 44, 30, 255), width=4 * SS)
    idraw.line(pts([(544, 368), (592, 376)]), fill=(20, 44, 30, 255), width=4 * SS)
    idraw.rectangle([p(223, 398), p(235, 508)], fill=(14, 38, 22, 255))
    idraw.rectangle([p(241, 386), p(251, 512)], fill=(215, 224, 217, 255), outline=(90, 110, 96, 255), width=1 * SS)
    idraw.rectangle([p(549, 386), p(559, 512)], fill=(155, 172, 158, 255), outline=(65, 85, 70, 255), width=1 * SS)
    idraw.rectangle([p(565, 412), p(578, 466)], fill=(10, 32, 18, 255))

    idraw.polygon(pts([(252, 362), (286, 322), (350, 358), (350, 518), (252, 520)]), fill=(242, 246, 243, 255), outline=(24, 48, 32, 255), width=3 * SS)
    idraw.polygon(pts([(450, 358), (514, 322), (548, 362), (548, 520), (450, 518)]), fill=(206, 216, 208, 255), outline=(24, 48, 32, 255), width=3 * SS)
    idraw.polygon(pts([(286, 332), (346, 364), (346, 514), (286, 514)]), fill=(222, 230, 224, 255))
    idraw.polygon(pts([(454, 364), (514, 332), (514, 514), (454, 514)]), fill=(176, 192, 180, 255))

    idraw.line(pts([(244, 366), (286, 318), (350, 356)]), fill=(18, 42, 28, 255), width=5 * SS)
    idraw.line(pts([(250, 373), (286, 332), (346, 365)]), fill=(72, 96, 80, 255), width=2 * SS)
    idraw.line(pts([(450, 356), (514, 318), (556, 366)]), fill=(18, 42, 28, 255), width=5 * SS)
    idraw.line(pts([(454, 365), (514, 332), (550, 373)]), fill=(72, 96, 80, 255), width=2 * SS)

    idraw.ellipse([p(270, 388), p(346, 496)], fill=(12, 134, 50, 255), outline=(8, 92, 34, 255), width=2 * SS)
    idraw.ellipse([p(454, 388), p(530, 496)], fill=(10, 118, 44, 255), outline=(7, 82, 30, 255), width=2 * SS)

    def make_arch_poly(xc, y_top, y_bot, w_half):
        pts_a = [(xc + w_half * math.cos(math.radians(a)), y_top + w_half + w_half * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        pts_a.extend([(xc + w_half, y_bot), (xc - w_half, y_bot)])
        return pts(pts_a)

    idraw.polygon(make_arch_poly(310, 418, 514, 22), fill=(4, 34, 14, 255), outline=(18, 68, 34, 255), width=2 * SS)
    idraw.polygon(make_arch_poly(490, 418, 514, 22), fill=(4, 34, 14, 255), outline=(18, 68, 34, 255), width=2 * SS)

    idraw.rectangle([p(344, 342), p(456, 514)], fill=(248, 250, 248, 255), outline=(22, 46, 32, 255), width=3 * SS)
    idraw.rectangle([p(400, 345), p(453, 512)], fill=(224, 232, 226, 255))
    idraw.rectangle([p(348, 346), p(366, 510)], fill=(254, 255, 254, 255), outline=(85, 105, 90, 255), width=2 * SS)
    idraw.rectangle([p(434, 346), p(452, 510)], fill=(212, 222, 214, 255), outline=(65, 85, 70, 255), width=2 * SS)
    idraw.rectangle([p(255, 364), p(270, 516)], fill=(252, 254, 252, 255), outline=(85, 105, 90, 255), width=2 * SS)

    idraw.polygon(make_arch_poly(400, 368, 510, 28), fill=(182, 198, 186, 255), outline=(45, 68, 52, 255), width=2 * SS)
    idraw.polygon(make_arch_poly(400, 404, 510, 22), fill=(4, 36, 15, 255), outline=(16, 62, 30, 255), width=2 * SS)

    idraw.rectangle([p(340, 328), p(460, 343)], fill=(218, 212, 178, 255), outline=(24, 48, 32, 255), width=3 * SS)
    idraw.line(pts([(336, 336), (464, 336)]), fill=(145, 140, 110, 255), width=2 * SS)

    dome_pts = [(400 - 44 * math.cos(math.radians(deg)) * (1.0 + 0.20 * math.sin(math.radians(deg + 28))), 294 + 34 * math.sin(math.radians(deg))) for deg in range(-90, 91, 4)]
    dome_pts += [(400 + 44 * math.cos(math.radians(deg)) * (1.0 + 0.20 * math.sin(math.radians(deg + 28))), 294 + 34 * math.sin(math.radians(deg))) for deg in range(90, -91, -4)]
    dome_mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(dome_mask).polygon(pts(dome_pts), fill=255)
    dome_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ddraw = ImageDraw.Draw(dome_layer)
    ddraw.polygon(pts(dome_pts), fill=(6, 78, 32, 255))
    for rad_step in range(44, 2, -2):
        t = (44 - rad_step) / 42.0
        ddraw.ellipse([p(384 - rad_step * 0.95, 286 - rad_step * 0.75), p(384 + rad_step * 0.95, 286 + rad_step * 0.75)], fill=(int(6 + 95 * (t ** 1.6)), int(82 + 145 * (t ** 1.3)), int(34 + 90 * (t ** 1.5)), 255))
    inner.paste(dome_layer, (0, 0), dome_mask)
    idraw.polygon(pts(dome_pts), outline=(6, 44, 18, 255), width=3 * SS)

    idraw.polygon(pts([(400, 208), (394, 260), (406, 260)]), fill=(20, 48, 30, 255))
    idraw.ellipse([p(394, 232), p(406, 244)], fill=(32, 66, 44, 255), outline=(14, 34, 22, 255), width=1 * SS)
    idraw.ellipse([p(396, 218), p(404, 226)], fill=(45, 82, 56, 255))

    idraw.polygon(pts([(192, 534), (336, 510), (332, 534), (192, 548)]), fill=(248, 250, 246, 255), outline=(26, 44, 30, 255), width=3 * SS)
    idraw.polygon(pts([(464, 510), (608, 534), (608, 548), (468, 534)]), fill=(218, 226, 218, 255), outline=(26, 44, 30, 255), width=3 * SS)
    idraw.polygon(pts([(196, 546), (332, 532), (328, 546), (196, 554)]), fill=(72, 56, 18, 255))
    idraw.polygon(pts([(468, 532), (604, 546), (604, 554), (472, 546)]), fill=(58, 44, 14, 255))

    idraw.polygon(pts([(264, 568), (330, 536), (400, 558), (470, 536), (536, 568), (470, 552), (400, 576), (330, 552)]), fill=(202, 164, 24, 255), outline=(38, 30, 6, 255), width=3 * SS)
    idraw.polygon(pts([(308, 544), (398, 552), (398, 560), (304, 552)]), fill=(210, 216, 208, 255), outline=(28, 42, 32, 255), width=2 * SS)
    idraw.polygon(pts([(402, 552), (492, 544), (496, 552), (402, 560)]), fill=(195, 204, 194, 255), outline=(28, 42, 32, 255), width=2 * SS)
    idraw.polygon(pts([(312, 542), (344, 484), (398, 488), (398, 550)]), fill=(255, 255, 255, 255), outline=(22, 38, 28, 255), width=3 * SS)
    idraw.polygon(pts([(402, 488), (456, 484), (488, 542), (402, 550)]), fill=(250, 252, 250, 255), outline=(22, 38, 28, 255), width=3 * SS)
    idraw.line(pts([(400, 486), (400, 556)]), fill=(18, 34, 24, 255), width=4 * SS)
    for ly in [500, 512, 524, 535]:
        idraw.line(pts([(344, ly), (388, ly + 2)]), fill=(148, 163, 154, 255), width=2 * SS)
        idraw.line(pts([(412, ly + 2), (456, ly)]), fill=(148, 163, 154, 255), width=2 * SS)

    inner_mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(inner_mask).ellipse([p(400 - 258, 400 - 258), p(400 + 258, 400 + 258)], fill=255)
    img.paste(inner, (0, 0), inner_mask)
    draw.ellipse([p(400 - 264, 400 - 264), p(400 + 264, 400 + 264)], outline=(9, 68, 33, 255), width=9 * SS)

    def draw_curved_text_ss(base_img, text, radius, font_size, color, top=True, tracking=1.05):
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        dummy = ImageDraw.Draw(base_img)
        char_widths = [dummy.textlength(ch, font=font) * tracking for ch in text]
        total_angle = (sum(char_widths) / radius) * (180.0 / math.pi)
        curr_angle = (-90.0 - total_angle / 2.0) if top else (90.0 + total_angle / 2.0)
        for ch, cw in zip(text, char_widths):
            ch_angle = (cw / 2.0 / radius) * (180.0 / math.pi)
            angle_deg = (curr_angle + ch_angle) if top else (curr_angle - ch_angle)
            curr_angle = (curr_angle + ch_angle * 2.0) if top else (curr_angle - ch_angle * 2.0)
            rad = math.radians(angle_deg)
            x, y = C + radius * math.cos(rad), C + radius * math.sin(rad)
            box_s = int(font_size * 2.6)
            ch_im = Image.new("RGBA", (box_s, box_s), (0, 0, 0, 0))
            ch_draw = ImageDraw.Draw(ch_im)
            bbox = ch_draw.textbbox((0, 0), ch, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            ch_draw.text((box_s / 2 - tw / 2 - bbox[0], box_s / 2 - th / 2 - bbox[1]), ch, font=font, fill=color)
            rot_deg = -(angle_deg + 90.0) if top else -(angle_deg - 90.0)
            base_img.alpha_composite(ch_im.rotate(rot_deg, resample=Image.BICUBIC, expand=False), (int(round(x - box_s / 2)), int(round(y - box_s / 2))))

    draw_curved_text_ss(img, "PESANTREN MODERN", radius=315 * SS, font_size=58 * SS, color=(12, 112, 52, 255), top=True, tracking=1.06)
    draw_curved_text_ss(img, "TGK. CHIEK OEMAR DIYAN", radius=316 * SS, font_size=40 * SS, color=(9, 44, 22, 255), top=False, tracking=1.05)

    for ang in [175.5, 4.5]:
        rad = math.radians(ang)
        dx, dy = C + 315 * SS * math.cos(rad), C + 315 * SS * math.sin(rad)
        r_d = 10.5 * SS
        draw.polygon([(dx, dy - r_d), (dx + r_d, dy), (dx, dy + r_d), (dx - r_d, dy)], fill=(12, 112, 52, 255))

    img.resize((OUT, OUT), Image.LANCZOS).save(out_path)

generate_crisp_logo(os.path.join(TEX, "mading_logo.png"))

photo_boxes_x = [
    (22, 155),
    (162, 305),
    (311, 454),
    (461, 604),
    (610, 753),
    (759, 903),
    (909, 1077),
    (1083, 1254),
]
for idx, (x0, x1) in enumerate(photo_boxes_x, start=1):
    # Crop only the building photo area (y: 778..821), excluding the old label bar at y: 822..861
    p_crop = ex_im.crop((x0, 778, x1, 821 if idx < 8 else 858))
    p_crop = ImageEnhance.Sharpness(p_crop).enhance(1.3)
    p_crop = p_crop.resize((p_crop.width * 2, p_crop.height * 2), Image.LANCZOS)
    p_crop.save(os.path.join(TEX, f"gedung_{idx}.jpg"), quality=92)

# ---------------------------------------------------------------------------
# 2. Load Campus Geospatial Data & Satellite Orthophoto
# ---------------------------------------------------------------------------
campus = json.load(open(os.path.join(PUB, "data", "campus.json"), encoding="utf-8"))
sat_im = Image.open(os.path.join(TEX, "satellite.jpg")).convert("RGB")
sw, sh = sat_im.size

sat_meta = campus["satellite"]
sx0, sx1, sz0, sz1 = sat_meta["x0"], sat_meta["x1"], sat_meta["z0"], sat_meta["z1"]

b_xs = [p[0] for p in campus["boundary"]]
b_zs = [p[1] for p in campus["boundary"]]
cx_world = (min(b_xs) + max(b_xs)) / 2.0
cz_world = (min(b_zs) + max(b_zs)) / 2.0

# Match exact container aspect ratios so 0%..100% marker coordinates have zero object-fit crop offset
# Use common world bounding box with aspect ratio 0.92 and render both panels cleanly, or per-panel bounds:
span_z = (max(b_zs) - min(b_zs)) + 86.0
min_z, max_z = cz_world - span_z / 2.0, cz_world + span_z / 2.0

# Ilustrasi panel aspect = 1.040, Satelit panel aspect = 0.814
# Let's use a helper to render a map for any given aspect ratio
span_x = span_z * 1.040
min_x, max_x = cx_world - span_x / 2.0, cx_world + span_x / 2.0

MW = 1560
MH = 1500

def world_to_map(x, z):
    px = (x - min_x) / (max_x - min_x) * MW
    py = (z - min_z) / (max_z - min_z) * MH
    return px, py

def poly_to_map(ring):
    return np.array([[int(round(world_to_map(p[0], p[1])[0])), int(round(world_to_map(p[0], p[1])[1]))] for p in ring], np.int32)

u0 = (min_x - sx0) / (sx1 - sx0)
u1 = (max_x - sx0) / (sx1 - sx0)
v0 = (min_z - sz0) / (sz1 - sz0)
v1 = (max_z - sz0) / (sz1 - sz0)

sat_crop = sat_im.crop((int(u0 * sw), int(v0 * sh), int(u1 * sw), int(v1 * sh))).resize((MW, MH), Image.LANCZOS)
sat_bgr = cv2.cvtColor(np.array(sat_crop), cv2.COLOR_RGB2BGR)

def get_building_style(loc_id):
    if loc_id in (4, 17):
        return {"fill": (22, 138, 66), "ridge": (15, 98, 46), "edge": (240, 253, 244), "kind": "dome"}
    elif loc_id in (3, 10, 13, 16, 22):
        return {"fill": (37, 99, 235), "ridge": (29, 78, 216), "edge": (219, 234, 254), "kind": "hip"}
    elif loc_id in (6, 9):
        return {"fill": (245, 130, 32), "ridge": (194, 90, 12), "edge": (255, 237, 213), "kind": "hip"}
    elif loc_id in (18, 21, 12, 20):
        return {"fill": (220, 48, 48), "ridge": (175, 28, 28), "edge": (254, 226, 226), "kind": "hip"}
    else:
        return {"fill": (110, 122, 138), "ridge": (75, 85, 99), "edge": (241, 245, 249), "kind": "hip"}

def draw_roof_3d(canvas_bgr, bld, style, is_satellite=False):
    ring_pts = poly_to_map(bld["outer"])
    hole_pts = [poly_to_map(h) for h in bld.get("holes", [])]

    bld_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(bld_mask, [ring_pts], 255)
    for hp in hole_pts:
        cv2.fillPoly(bld_mask, [hp], 0)

    # Drop shadow
    shadow_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(shadow_mask, [ring_pts + np.array([[6, 7]], dtype=np.int32)], 255)
    for hp in hole_pts:
        cv2.fillPoly(shadow_mask, [hp + np.array([[6, 7]], dtype=np.int32)], 0)
    sh_only = (shadow_mask > 0) & (bld_mask == 0)
    canvas_bgr[sh_only] = (canvas_bgr[sh_only] * 0.55).astype(np.uint8)

    r, g, b = style["fill"]
    rr, rg, rb = style["ridge"]
    er, eg, eb = style["edge"]

    # Fill outer roof slope
    if is_satellite:
        canvas_bgr[bld_mask > 0] = (canvas_bgr[bld_mask > 0] * 0.18 + np.array([b, g, r]) * 0.82).astype(np.uint8)
    else:
        canvas_bgr[bld_mask > 0] = (b, g, r)

    # Inner bevel/ridge area via morphological erosion of bld_mask (respects U-shapes and L-shapes!)
    kernel_size = max(7, int(min(cv2.boundingRect(ring_pts)[2:4]) * 0.24))
    if kernel_size % 2 == 0:
        kernel_size += 1
    inner_mask = cv2.erode(bld_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)))
    canvas_bgr[inner_mask > 0] = (rb, rg, rr)

    # Draw crisp inner ridge contour and outer roof contour
    in_cnts, _ = cv2.findContours(inner_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(canvas_bgr, in_cnts, -1, (int((b+eb)/2), int((g+eg)/2), int((r+er)/2)), 2, cv2.LINE_AA)

    cv2.polylines(canvas_bgr, [ring_pts], True, (eb, eg, er), 2, cv2.LINE_AA)
    for hp in hole_pts:
        cv2.polylines(canvas_bgr, [hp], True, (eb, eg, er), 2, cv2.LINE_AA)

    if style["kind"] == "dome":
        rect = cv2.minAreaRect(ring_pts.astype(np.float32))
        (cx, cy), (rw, rh), _ = rect
        rad = int(max(11, min(rw, rh) * 0.34))
        cv2.circle(canvas_bgr, (int(cx), int(cy)), rad + 2, (240, 255, 240), -1, cv2.LINE_AA)
        cv2.circle(canvas_bgr, (int(cx), int(cy)), rad, (55, 175, 90), -1, cv2.LINE_AA)
        cv2.circle(canvas_bgr, (int(cx) - rad // 4, int(cy) - rad // 4), max(2, rad // 3), (110, 215, 140), -1, cv2.LINE_AA)
        cv2.circle(canvas_bgr, (int(cx), int(cy)), 3, (30, 215, 250), -1, cv2.LINE_AA)

def draw_court_markings(canvas_bgr, ring_pts, loc_id, is_satellite=False):
    mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(mask, [ring_pts], 255)

    if not is_satellite:
        canvas_bgr[mask > 0] = (68, 165, 72)

    # For L-shaped Lapangan Pesantren (#23), draw mowed lawn stripes clipped strictly inside mask
    if loc_id == 23:
        x, y, w, h = cv2.boundingRect(ring_pts)
        stripe_w = max(12, w // 14)
        for sx in range(x, x + w, stripe_w * 2):
            s_mask = np.zeros_like(mask)
            cv2.rectangle(s_mask, (sx, y), (sx + stripe_w, y + h), 255, -1)
            both = (mask > 0) & (s_mask > 0)
            if not is_satellite:
                canvas_bgr[both] = (82, 180, 86)
        # Draw white border & main west football pitch inside mask
        cv2.polylines(canvas_bgr, [ring_pts], True, (245, 250, 245), 2, cv2.LINE_AA)
        return

    rect = cv2.minAreaRect(ring_pts.astype(np.float32))
    (cx, cy), (rw, rh), angle = rect
    if rw > rh:
        rw, rh = rh, rw
        angle += 90.0

    rad_a = math.radians(angle)
    cos_a, sin_a = math.cos(rad_a), math.sin(rad_a)

    def local_to_px(u, v):
        px = cx + u * cos_a - v * sin_a
        py = cy + u * sin_a + v * cos_a
        return int(round(px)), int(round(py))

    if not is_satellite:
        n_stripes = 6
        for s in range(n_stripes):
            if s % 2 == 0:
                v0_s = -rh * 0.48 + s * (rh * 0.96 / n_stripes)
                v1_s = v0_s + (rh * 0.96 / n_stripes)
                s_poly = np.array([
                    local_to_px(-rw * 0.48, v0_s),
                    local_to_px(rw * 0.48, v0_s),
                    local_to_px(rw * 0.48, v1_s),
                    local_to_px(-rw * 0.48, v1_s),
                ], np.int32)
                stripe_mask = np.zeros_like(mask)
                cv2.fillPoly(stripe_mask, [s_poly], 255)
                both = (mask > 0) & (stripe_mask > 0)
                canvas_bgr[both] = (82, 182, 86)

    # Draw court markings onto a temporary layer and clip to `mask`
    line_layer = canvas_bgr.copy()
    cv2.polylines(line_layer, [ring_pts], True, (245, 250, 245), 2, cv2.LINE_AA)

    w_in, h_in = rw * 0.78, rh * 0.82
    corners = np.array([
        local_to_px(-w_in / 2, -h_in / 2),
        local_to_px(w_in / 2, -h_in / 2),
        local_to_px(w_in / 2, h_in / 2),
        local_to_px(-w_in / 2, h_in / 2),
    ], np.int32)
    cv2.polylines(line_layer, [corners], True, (250, 252, 250), 2, cv2.LINE_AA)
    cv2.line(line_layer, local_to_px(-w_in / 2, 0), local_to_px(w_in / 2, 0), (250, 252, 250), 2, cv2.LINE_AA)
    cv2.circle(line_layer, (int(cx), int(cy)), int(min(w_in, h_in) * 0.16), (250, 252, 250), 2, cv2.LINE_AA)

    canvas_bgr[mask > 0] = line_layer[mask > 0]

# ---------------------------------------------------------------------------
# 3. Render DENAH ILUSTRASI (public/textures/mading_ilustrasi.jpg)
# ---------------------------------------------------------------------------
ilus = sat_bgr.copy()
hsv = cv2.cvtColor(ilus, cv2.COLOR_BGR2HSV).astype(np.float32)
hsv[..., 0] = np.clip(hsv[..., 0] * 0.6 + 22, 32, 68)
hsv[..., 1] = np.clip(hsv[..., 1] * 1.45 + 35, 60, 210)
hsv[..., 2] = np.clip(hsv[..., 2] * 1.08 + 18, 55, 225)
ilus = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
ilus = cv2.bilateralFilter(ilus, 9, 45, 45)

boundary_pts = poly_to_map(campus["boundary"])
campus_mask = np.zeros((MH, MW), dtype=np.uint8)
cv2.fillPoly(campus_mask, [boundary_pts], 255)

grass_base = np.full_like(ilus, (118, 188, 126))
ilus = np.where(
    campus_mask[..., None] > 0,
    (ilus * 0.25 + grass_base * 0.75).astype(np.uint8),
    (ilus * 0.80 + grass_base * 0.20).astype(np.uint8),
)

for f_poly in campus.get("forest", []):
    f_pts = poly_to_map(f_poly["outer"])
    f_holes = [poly_to_map(h) for h in f_poly.get("holes", [])]
    f_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(f_mask, [f_pts], 255)
    for fh in f_holes:
        cv2.fillPoly(f_mask, [fh], 0)
    ilus[f_mask > 0] = (ilus[f_mask > 0] * 0.72 + np.array([62, 135, 68]) * 0.28).astype(np.uint8)

for r_poly in campus.get("rivers", []):
    r_pts = poly_to_map(r_poly["outer"])
    cv2.fillPoly(ilus, [r_pts], (65, 86, 102))
    cv2.polylines(ilus, [r_pts], True, (48, 66, 80), 3, cv2.LINE_AA)

for rd in campus.get("roadsInternal", []):
    r_pts = poly_to_map(rd["outer"])
    r_holes = [poly_to_map(h) for h in rd.get("holes", [])]
    rd_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(rd_mask, [r_pts], 255)
    for rh in r_holes:
        cv2.fillPoly(rd_mask, [rh], 0)
    rd_border = cv2.dilate(rd_mask, np.ones((5, 5), np.uint8))
    ilus[(rd_border > 0) & (rd_mask == 0)] = (45, 165, 210)
    ilus[rd_mask > 0] = (20, 215, 248)

for rd in campus.get("roadsMain", []):
    r_pts = poly_to_map(rd["outer"])
    r_holes = [poly_to_map(h) for h in rd.get("holes", [])]
    rd_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(rd_mask, [r_pts], 255)
    for rh in r_holes:
        cv2.fillPoly(rd_mask, [rh], 0)
    ilus[rd_mask > 0] = (225, 232, 238)

for rd in campus.get("roadsCore", []):
    r_pts = poly_to_map(rd["outer"])
    r_holes = [poly_to_map(h) for h in rd.get("holes", [])]
    rd_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(rd_mask, [r_pts], 255)
    for rh in r_holes:
        cv2.fillPoly(rd_mask, [rh], 0)
    ilus[rd_mask > 0] = (42, 46, 52)

for glb in campus.get("globe", []):
    g_pts = poly_to_map(glb["outer"])
    cv2.fillPoly(ilus, [g_pts], (225, 155, 45))
    cv2.polylines(ilus, [g_pts], True, (255, 255, 255), 2, cv2.LINE_AA)

sorted_trees = sorted(campus.get("trees", []), key=lambda t: t[1])
for t in sorted_trees:
    tx, tz, kind, scale, cls = t
    px, py = world_to_map(tx, tz)
    ix, iy = int(round(px)), int(round(py))
    rad = int(max(4, round(scale * (4.8 if cls == 2 else 4.0))))

    cv2.circle(ilus, (ix + 3, iy + 3), rad, (32, 68, 35), -1, cv2.LINE_AA)
    if kind == 1:
        cv2.circle(ilus, (ix, iy), rad, (42, 138, 52), -1, cv2.LINE_AA)
        cv2.circle(ilus, (ix - 1, iy - 1), max(2, rad // 2), (75, 178, 82), -1, cv2.LINE_AA)
    else:
        c_main = (38, 122, 46) if (ix + iy) % 2 == 0 else (46, 138, 54)
        cv2.circle(ilus, (ix, iy), rad, c_main, -1, cv2.LINE_AA)
        cv2.circle(ilus, (ix - rad // 3, iy - rad // 3), max(2, int(rad * 0.55)), (72, 168, 78), -1, cv2.LINE_AA)

# Buildings & Courts
for bld in campus.get("buildings", []):
    style = get_building_style(bld.get("loc"))
    draw_roof_3d(ilus, bld, style, is_satellite=False)

for fld in campus.get("fields", []):
    f_pts = poly_to_map(fld["outer"])
    draw_court_markings(ilus, f_pts, fld.get("loc"), is_satellite=False)

# Bold Campus Outer Boundary Line (White casing + Red/Black line)
cv2.polylines(ilus, [boundary_pts], True, (255, 255, 255), 9, cv2.LINE_AA)
cv2.polylines(ilus, [boundary_pts], True, (35, 35, 230), 5, cv2.LINE_AA)

Image.fromarray(cv2.cvtColor(ilus, cv2.COLOR_BGR2RGB)).save(os.path.join(TEX, "mading_ilustrasi.jpg"), quality=92)
print("Saved mading_ilustrasi.jpg", (MW, MH))

# ---------------------------------------------------------------------------
# 4. Render DENAH SATELIT (public/textures/mading_satelit.jpg)
# ---------------------------------------------------------------------------
sat_canvas = sat_bgr.copy()
sat_pil = ImageEnhance.Contrast(ImageEnhance.Sharpness(Image.fromarray(cv2.cvtColor(sat_canvas, cv2.COLOR_BGR2RGB))).enhance(1.35)).enhance(1.12)
sat_canvas = cv2.cvtColor(np.array(sat_pil), cv2.COLOR_RGB2BGR)

outside_mask = campus_mask == 0
sat_canvas[outside_mask] = (sat_canvas[outside_mask] * 0.72).astype(np.uint8)

# Subtle internal road overlay on satellite map (matching Example-Desain.jpeg)
for rd in campus.get("roadsInternal", []):
    r_pts = poly_to_map(rd["outer"])
    r_holes = [poly_to_map(h) for h in rd.get("holes", [])]
    rd_mask = np.zeros((MH, MW), dtype=np.uint8)
    cv2.fillPoly(rd_mask, [r_pts], 255)
    for rh in r_holes:
        cv2.fillPoly(rd_mask, [rh], 0)
    sat_canvas[rd_mask > 0] = (sat_canvas[rd_mask > 0] * 0.55 + np.array([140, 165, 180]) * 0.45).astype(np.uint8)

for bld in campus.get("buildings", []):
    style = get_building_style(bld.get("loc"))
    draw_roof_3d(sat_canvas, bld, style, is_satellite=True)

for fld in campus.get("fields", []):
    f_pts = poly_to_map(fld["outer"])
    draw_court_markings(sat_canvas, f_pts, fld.get("loc"), is_satellite=True)

# Bold Campus Outer Boundary Line on Satellite Map
cv2.polylines(sat_canvas, [boundary_pts], True, (255, 255, 255), 9, cv2.LINE_AA)
cv2.polylines(sat_canvas, [boundary_pts], True, (25, 25, 25), 5, cv2.LINE_AA)

# Crop sat_canvas horizontally to match Column 2 aspect ratio (0.814 -> 1221 x 1500)
SAT_W = int(round(MH * 0.814))
crop_x0 = (MW - SAT_W) // 2
sat_cropped = sat_canvas[:, crop_x0:crop_x0 + SAT_W]

Image.fromarray(cv2.cvtColor(sat_cropped, cv2.COLOR_BGR2RGB)).save(os.path.join(TEX, "mading_satelit.jpg"), quality=92)
print("Saved mading_satelit.jpg", (SAT_W, MH))

marker_pcts = []
for loc in sorted(campus["locations"], key=lambda l: l["id"]):
    px, py = world_to_map(loc["x"], loc["z"])
    lid = loc["id"]
    if lid in (4, 17):
        cat_color = "#16803c"
    elif lid in (3, 10, 13, 16, 22):
        cat_color = "#2563eb"
    elif lid in (6, 9):
        cat_color = "#f97316"
    elif lid in (18, 21, 12, 20):
        cat_color = "#dc2626"
    elif lid in (8, 11, 23, 24, 25, 26):
        cat_color = "#15803d"
    else:
        cat_color = "#475569"

    marker_pcts.append({
        "id": lid,
        "name": loc["name"],
        "short": loc.get("short", loc["name"]),
        "category": loc.get("category", "Fasilitas"),
        "desc": loc.get("desc", ""),
        "lat": loc["lat"],
        "lng": loc["lng"],
        "left": round(px / MW * 100, 2),
        "top": round(py / MH * 100, 2),
        "leftSat": round((px - crop_x0) / SAT_W * 100, 2),
        "topSat": round(py / MH * 100, 2),
        "color": cat_color,
    })

json.dump(marker_pcts, open(os.path.join(PUB, "data", "mading_markers.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("Saved mading_markers.json with", len(marker_pcts), "locations")
