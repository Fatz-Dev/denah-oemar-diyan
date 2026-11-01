import base64, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "generateweb-sebelumnya", "denah_3d_oemar_diyan.html")
SAT_PATH = os.path.join(ROOT, "public", "textures", "satellite.jpg")

content = open(SRC, "encoding='utf-8'").read() if False else open(SRC, encoding="utf-8").read()

# Enhance createSatelliteGroundTexture to support local high-res satellite image
target = '''        function createSatelliteGroundTexture() {
            // High-res procedural satellite + Esri World Imagery hybrid canvas
            const canvas = document.createElement('canvas');
            canvas.width = 1024;
            canvas.height = 1024;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#2d4c2b';
            ctx.fillRect(0, 0, 1024, 1024);
            for (let i = 0; i < 25000; i++) {
                ctx.fillStyle = i % 2 === 0 ? 'rgba(68, 108, 53, 0.35)' : 'rgba(34, 62, 30, 0.35)';
                ctx.fillRect(Math.random() * 1024, Math.random() * 1024, 4, 4);
            }
            const tex = new THREE.CanvasTexture(canvas);
            // Also asynchronously load real Esri satellite tile for 5.3992, 95.4358 (Zoom 17)
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                ctx.drawImage(img, 0, 0, 1024, 1024);
                tex.needsUpdate = true;
            };
            img.src = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/16/31819/50142";
            tex.wrapS = THREE.ClampToEdgeWrapping;
            tex.wrapT = THREE.ClampToEdgeWrapping;
            return tex;
        }'''

replacement = '''        function createSatelliteGroundTexture() {
            // High-res procedural satellite + Esri World Imagery hybrid canvas
            const canvas = document.createElement('canvas');
            canvas.width = 1024;
            canvas.height = 1024;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#2d4c2b';
            ctx.fillRect(0, 0, 1024, 1024);
            for (let i = 0; i < 25000; i++) {
                ctx.fillStyle = i % 2 === 0 ? 'rgba(68, 108, 53, 0.35)' : 'rgba(34, 62, 30, 0.35)';
                ctx.fillRect(Math.random() * 1024, Math.random() * 1024, 4, 4);
            }
            const tex = new THREE.CanvasTexture(canvas);
            // Load high-resolution orthophoto with fallback
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                ctx.drawImage(img, 0, 0, 1024, 1024);
                tex.needsUpdate = true;
            };
            img.onerror = () => {
                const online = new Image();
                online.crossOrigin = "anonymous";
                online.onload = () => {
                    ctx.drawImage(online, 0, 0, 1024, 1024);
                    tex.needsUpdate = true;
                };
                online.src = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/16/31819/50142";
            };
            img.src = "public/textures/satellite.jpg";
            tex.wrapS = THREE.ClampToEdgeWrapping;
            tex.wrapT = THREE.ClampToEdgeWrapping;
            return tex;
        }'''

if target in content:
    content_updated = content.replace(target, replacement)
else:
    print("WARNING: target not matched exactly, using original")
    content_updated = content

# 1. Write to root index.html
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(content_updated)
print("Updated index.html")

# 2. Write to dist/index.html
os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
open(os.path.join(ROOT, "dist", "index.html"), "w", encoding="utf-8").write(content_updated.replace("public/textures/", "textures/"))
print("Updated dist/index.html")

# 3. Create standalone denah_3d_offline.html with base64 inlined satellite image
sat_bytes = open(SAT_PATH, "rb").read()
sat_b64 = "data:image/jpeg;base64," + base64.b64encode(sat_bytes).decode("ascii")
content_offline = content_updated.replace('"public/textures/satellite.jpg"', f'"{sat_b64}"')
open(os.path.join(ROOT, "denah_3d_offline.html"), "w", encoding="utf-8").write(content_offline)
print(f"Generated denah_3d_offline.html ({os.path.getsize(os.path.join(ROOT, 'denah_3d_offline.html')):,} bytes)")
