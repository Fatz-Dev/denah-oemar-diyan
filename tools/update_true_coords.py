"""Update index.html and denah_3d_offline.html with exact building coordinates
from Pemetaan.png, true road network, and North-Up default camera view.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")

content = open(INDEX_PATH, encoding="utf-8").read()

# 1. Update LOCATIONS array with exact Pemetaan.png coordinates
new_locations_block = """        const LOCATIONS = [
            { id: 1,  shortLabel: "Gerbang",            fullName: "1. Gerbang Utama", cat: "Akses Utama", lat: 5.401452, lng: 95.434851, x: -8.9,  z: -112.1, y: 7 },
            { id: 2,  shortLabel: "Pos Satpam",         fullName: "2. Pos Satpam", cat: "Keamanan", lat: 5.401284, lng: 95.435048, x: -2.7,  z: -105.4, y: 5 },
            { id: 3,  shortLabel: "MTsN",               fullName: "3. Sekolah MTsN", cat: "Gedung Sekolah", lat: 5.400951, lng: 95.435552, x: 19.5,  z: -86.8,  y: 9 },
            { id: 4,  shortLabel: "Masjid",             fullName: "4. Masjid Baburrayyan", cat: "Ibadah", lat: 5.400825, lng: 95.434720, x: -14.9, z: -77.7,  y: 13 },
            { id: 5,  shortLabel: "Food Court",         fullName: "5. Kantin dan Food Court", cat: "Konsumsi", lat: 5.400104, lng: 95.436054, x: 36.4,  z: -42.4,  y: 8 },
            { id: 6,  shortLabel: "Asrama Putra",       fullName: "6. Asrama Putra (Utara)", cat: "Asrama Putra", lat: 5.400320, lng: 95.434422, x: -25.0, z: -51.5,  y: 12 },
            { id: 7,  shortLabel: "Tugu Globe",         fullName: "7. Tugu Globe", cat: "Landmark", lat: 5.399682, lng: 95.436081, x: 37.0,  z: -23.3,  y: 7 },
            { id: 8,  shortLabel: "Lapangan Basket",    fullName: "8. Lapangan Basket", cat: "Olahraga", lat: 5.399620, lng: 95.435780, x: 26.2,  z: -20.2,  y: 2 },
            { id: 9,  shortLabel: "Asrama Putra",       fullName: "9. Asrama Putra (Barat)", cat: "Asrama Putra", lat: 5.399552, lng: 95.434150, x: -45.3, z: -17.4,  y: 10 },
            { id: 10, shortLabel: "Sekolah GTS",        fullName: "10. Gedung Sekolah GTS", cat: "Gedung Sekolah", lat: 5.399250, lng: 95.436482, x: 56.3,  z: -4.4,   y: 11 },
            { id: 11, shortLabel: "Lapangan Bola",      fullName: "11. Lapangan Bola / Lapangan Upacara", cat: "Olahraga & Upacara", lat: 5.399284, lng: 95.436120, x: 39.5,  z: -1.7,   y: 2 },
            { id: 12, shortLabel: "Mess Ustad",         fullName: "12. Mess Ustad", cat: "Kediaman Staf", lat: 5.399251, lng: 95.435721, x: 20.8,  z: -4.1,   y: 7 },
            { id: 13, shortLabel: "TU & Perpustakaan",  fullName: "13. Ruang TU MA & MTsN, Perpustakaan, R. Guru & Aula", cat: "Pusat Akademik", lat: 5.398920, lng: 95.435580, x: 15.0,  z: 14.5,   y: 9 },
            { id: 14, shortLabel: "Administrasi",       fullName: "14. 2 Gedung Administrasi dan Ruang Turkey", cat: "Administrasi", lat: 5.398821, lng: 95.436050, x: 35.8,  z: 17.5,   y: 8 },
            { id: 15, shortLabel: "Ruang Makan Putra",  fullName: "15. Ruang Makan Putra", cat: "Konsumsi", lat: 5.398850, lng: 95.436680, x: 62.3,  z: 17.2,   y: 7 },
            { id: 16, shortLabel: "Gedung Turkey",      fullName: "16. Gedung Turkey / Gedung Sekolah", cat: "Gedung Sekolah", lat: 5.398422, lng: 95.435920, x: 29.3,  z: 36.6,   y: 8 },
            { id: 17, shortLabel: "Musalla Putri",      fullName: "17. Musalla Putri", cat: "Ibadah", lat: 5.398580, lng: 95.435622, x: 13.5,  z: 29.5,   y: 8 },
            { id: 18, shortLabel: "Asrama Putri",       fullName: "18. Asrama Putri (Tengah)", cat: "Asrama Putri", lat: 5.398150, lng: 95.435320, x: 4.5,   z: 51.0,   y: 9 },
            { id: 19, shortLabel: "Dapur Putri",        fullName: "19. 2 Ruang Dapur dan Ruang Makan Putri", cat: "Konsumsi", lat: 5.397920, lng: 95.436052, x: 33.0,  z: 65.0,   y: 8 },
            { id: 20, shortLabel: "Kantin Putri",       fullName: "20. Kantin Putri dan Mess Ustazah", cat: "Fasilitas Putri", lat: 5.397622, lng: 95.435250, x: -1.2,  z: 80.0,   y: 8 },
            { id: 21, shortLabel: "Asrama Putri",       fullName: "21. Asrama Putri (Selatan)", cat: "Asrama Putri", lat: 5.397924, lng: 95.434820, x: -19.4, z: 65.8,   y: 9 },
            { id: 22, shortLabel: "Aula STB",           fullName: "22. Aula STB", cat: "Aula Serbaguna", lat: 5.398152, lng: 95.434550, x: -30.9, z: 54.1,   y: 8 },
            { id: 23, shortLabel: "Lapangan Pesantren", fullName: "23. Lapangan Pesantren", cat: "Lapangan Utama", lat: 5.398650, lng: 95.434450, x: -36.0, z: 31.9,   y: 2 },
            { id: 24, shortLabel: "Bulu Tangkis",       fullName: "24. Lapangan Bulu Tangkis", cat: "Olahraga", lat: 5.400120, lng: 95.434620, x: -24.1, z: -44.3,  y: 2 },
            { id: 25, shortLabel: "Lapangan Asrama",    fullName: "25. Lapangan Asrama Putra", cat: "Olahraga", lat: 5.399550, lng: 95.433920, x: -50.5, z: -17.0,  y: 2 },
            { id: 26, shortLabel: "Lapangan Voli",      fullName: "26. Lapangan Voli", cat: "Olahraga", lat: 5.400720, lng: 95.434980, x: -5.2,  z: -74.0,  y: 2 }
        ];

        // Secondary sub-building labels for multi-building clusters
        const EXTRA_LABELS = [
            { id: 6,  shortLabel: "Asrama Putra",      x: -36.0, z: -50.0, y: 10 },
            { id: 13, shortLabel: "TU & Perpustakaan", x: 18.1,  z: 11.4,  y: 9 },
            { id: 18, shortLabel: "Asrama Putri",      x: 7.7,   z: 56.6,  y: 8 },
            { id: 19, shortLabel: "Dapur Putri",       x: 31.4,  z: 70.2,  y: 8 },
            { id: 19, shortLabel: "Dapur Putri",       x: 33.3,  z: 82.9,  y: 7 },
            { id: 20, shortLabel: "Kantin Putri",      x: -0.4,  z: 87.8,  y: 7 },
            { id: 21, shortLabel: "Asrama Putri",      x: -21.6, z: 70.3,  y: 9 }
        ];"""

content = re.sub(r'const LOCATIONS = \[.*?const EXTRA_LABELS = \[.*?\];', new_locations_block, content, flags=re.DOTALL)

# 2. Update default camera to start in North-Up (matching Pemetaan.png & preview.webp)
cam_state_old = """        // Camera Orbit State — Starts in Preview (1).webp Southeast Labeled Isometric View!
        const camState = {
            theta: 2.38,            // Rotated SE angle matching preview (1).webp
            phi: 0.92,              // Isometric pitch matching preview (1).webp
            radius: 262,
            target: new THREE.Vector3(2, 0, -2),
            targetTheta: 2.38,
            targetPhi: 0.92,
            targetRadius: 262,
            targetLookAt: new THREE.Vector3(2, 0, -2),"""

cam_state_new = """        // Camera Orbit State — Starts in True North-Up View (Matching Pemetaan.png & preview.webp)
        const camState = {
            theta: -0.18,           // True North orientation matching Pemetaan.png
            phi: 0.88,              // Isometric pitch matching preview.webp
            radius: 262,
            target: new THREE.Vector3(0, 0, 0),
            targetTheta: -0.18,
            targetPhi: 0.88,
            targetRadius: 262,
            targetLookAt: new THREE.Vector3(0, 0, 0),"""

content = content.replace(cam_state_old, cam_state_new)

# 3. Update buildAll26Buildings with exact coordinates from Pemetaan.png
buildings_code_new = """        function buildAll26Buildings() {
            const ROOF_LIGHT_GREY = 0xdbe2ea;
            const ROOF_MID_GREY   = 0x94a3b8;
            const ROOF_BLUE_SLATE = 0x7c8ea6;
            const DOME_GREEN      = 0x229954;

            // 1. GERBANG (North Entry Archway)
            const gateGroup = new THREE.Group();
            gateGroup.position.set(-8.9, 0.35, -112.1);
            gateGroup.rotation.y = 0.42;
            const pillarMat = new THREE.MeshLambertMaterial({ color: 0xf8fafc });
            const pL = new THREE.Mesh(new THREE.BoxGeometry(1.5, 6.2, 1.5), pillarMat);
            pL.position.set(-3.4, 3.1, 0);
            const pR = new THREE.Mesh(new THREE.BoxGeometry(1.5, 6.2, 1.5), pillarMat);
            pR.position.set(3.4, 3.1, 0);
            const topBeam = new THREE.Mesh(new THREE.BoxGeometry(9.2, 1.4, 2.0), new THREE.MeshLambertMaterial({ color: 0xe2e8f0 }));
            topBeam.position.set(0, 6.2, 0);
            [pL, pR, topBeam].forEach(m => {
                m.castShadow = true;
                m.userData = { locationId: 1 };
                interactiveMeshes.push(m);
            });
            gateGroup.add(pL, pR, topBeam);
            scene.add(gateGroup);

            // 2. POS SATPAM
            build3DBuilding({ id: 2, x: -2.7, z: -105.4, w: 4.2, d: 4.8, h: 3.2, rotY: -0.45, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 1 });

            // 3. SEKOLAH MTsN (Angled along East Road)
            build3DBuilding({ id: 3, x: 19.5, z: -86.8, w: 30.0, d: 7.2, h: 6.5, rotY: -0.58, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });

            // 4. MASJID BABURRAYYAN (Main Mosque + Central Green Dome + Minaret Tower)
            const masjid = build3DBuilding({ id: 4, x: -14.9, z: -77.7, w: 16.0, d: 11.5, h: 5.6, rotY: 0.28, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 1 });
            const domeDrum = new THREE.Mesh(new THREE.CylinderGeometry(3.6, 3.8, 1.2, 24), new THREE.MeshLambertMaterial({ color: 0xf1f5f9 }));
            domeDrum.position.y = 6.2;
            const greenDome = new THREE.Mesh(
                new THREE.SphereGeometry(3.6, 24, 16, 0, Math.PI * 2, 0, Math.PI * 0.55),
                new THREE.MeshLambertMaterial({ color: DOME_GREEN })
            );
            greenDome.position.y = 6.6;
            greenDome.castShadow = true;
            greenDome.userData = { locationId: 4 };
            interactiveMeshes.push(greenDome);
            const minaretShaft = new THREE.Mesh(new THREE.BoxGeometry(1.6, 13.0, 1.6), new THREE.MeshLambertMaterial({ color: 0xf8fafc }));
            minaretShaft.position.set(7.0, 6.5, -4.5);
            minaretShaft.castShadow = true;
            const minaretCap = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2.6, 12), new THREE.MeshLambertMaterial({ color: DOME_GREEN }));
            minaretCap.position.set(7.0, 14.0, -4.5);
            masjid.add(domeDrum, greenDome, minaretShaft, minaretCap);

            // 5. FOOD COURT / KANTIN (East side)
            build3DBuilding({ id: 5, x: 36.4, z: -42.4, w: 12.0, d: 22.0, h: 5.0, rotY: -0.42, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 1 });

            // 6. ASRAMA PUTRA (UTARA) - Exact match to Pemetaan.png
            build3DBuilding({ id: 6, x: -21.6, z: -52.8, w: 28.0, d: 15.0, h: 9.2, rotY: 0.22, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 3 });
            build3DBuilding({ id: 6, x: -36.0, z: -49.9, w: 15.0, d: 15.0, h: 9.2, rotY: 0.22, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 3 });

            // 7. TUGU GLOBE (Triangular junction)
            const triPts = [[34.0, -26.0], [42.0, -23.0], [35.0, -18.0]];
            const triShape = createShapeFromCoords(triPts);
            const triGeo = new THREE.ExtrudeGeometry(triShape, { depth: 0.45, bevelEnabled: false });
            triGeo.rotateX(-Math.PI / 2);
            const triPool = new THREE.Mesh(triGeo, new THREE.MeshLambertMaterial({ color: 0x00b4d8 }));
            triPool.position.y = 0.25;
            scene.add(triPool);

            const globeGroup = new THREE.Group();
            globeGroup.position.set(37.0, 0.5, -23.3);
            const ped = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.5, 2.5, 16), new THREE.MeshLambertMaterial({ color: 0xf8fafc }));
            ped.position.y = 1.25;
            globeMesh = new THREE.Mesh(
                new THREE.SphereGeometry(1.85, 18, 16),
                new THREE.MeshLambertMaterial({ color: 0x0284c7 })
            );
            globeMesh.position.y = 3.8;
            const wireGlobe = new THREE.Mesh(
                new THREE.SphereGeometry(1.88, 12, 10),
                new THREE.MeshBasicMaterial({ color: 0xe0f2fe, wireframe: true, transparent: true, opacity: 0.45 })
            );
            globeMesh.add(wireGlobe);
            globeMesh.userData = { locationId: 7 };
            interactiveMeshes.push(globeMesh, ped);
            globeGroup.add(ped, globeMesh);
            scene.add(globeGroup);

            // 9. ASRAMA PUTRA (BARAT)
            build3DBuilding({ id: 9, x: -45.3, z: -17.4, w: 15.0, d: 18.0, h: 6.5, rotY: 0, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });

            // 10. GEDUNG SEKOLAH GTS (Long 3-story school along East road)
            build3DBuilding({ id: 10, x: 56.3, z: -4.4, w: 8.0, d: 33.0, h: 8.8, rotY: -0.38, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 3 });

            // 12. MESS USTAD
            build3DBuilding({ id: 12, x: 20.8, z: -4.1, w: 16.5, d: 8.5, h: 4.8, rotY: 0.08, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 1 });

            // 13. TU & PERPUSTAKAAN (Academic cluster)
            build3DBuilding({ id: 13, x: 18.1, z: 11.4, w: 7.0, d: 12.0, h: 6.4, rotY: 0.36, roofType: 'hipped', roofColor: ROOF_BLUE_SLATE, floors: 2 });
            build3DBuilding({ id: 13, x: 11.7, z: 11.8, w: 6.5, d: 12.0, h: 6.4, rotY: 0.36, roofType: 'hipped', roofColor: ROOF_BLUE_SLATE, floors: 2 });
            build3DBuilding({ id: 13, x: 15.6, z: 18.7, w: 6.0, d: 6.0,  h: 6.0, rotY: 0.36, roofType: 'hipped', roofColor: ROOF_BLUE_SLATE, floors: 2 });

            // 14. ADMINISTRASI
            build3DBuilding({ id: 14, x: 35.8, z: 17.5, w: 14.5, d: 6.0, h: 5.8, rotY: 0.14, roofType: 'hipped', roofColor: ROOF_BLUE_SLATE, floors: 2 });

            // 15. RUANG MAKAN PUTRA
            build3DBuilding({ id: 15, x: 62.3, z: 17.2, w: 12.0, d: 8.0, h: 5.2, rotY: -0.42, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 1 });

            // 16. GEDUNG TURKEY / GEDUNG SEKOLAH
            build3DBuilding({ id: 16, x: 29.3, z: 36.6, w: 5.5, d: 21.0, h: 6.0, rotY: 0.28, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });

            // 17. MUSALLA PUTRI (Square building with green dome)
            const musallaPutri = build3DBuilding({ id: 17, x: 13.5, z: 29.5, w: 7.5, d: 8.0, h: 4.5, rotY: 0.36, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 1 });
            const mpDome = new THREE.Mesh(
                new THREE.SphereGeometry(2.3, 20, 14, 0, Math.PI * 2, 0, Math.PI * 0.55),
                new THREE.MeshLambertMaterial({ color: DOME_GREEN })
            );
            mpDome.position.y = 4.6;
            mpDome.castShadow = true;
            mpDome.userData = { locationId: 17 };
            interactiveMeshes.push(mpDome);
            musallaPutri.add(mpDome);

            // 18. ASRAMA PUTRI (TENGAH)
            build3DBuilding({ id: 18, x: 2.6, z: 45.7, w: 6.0, d: 22.0, h: 6.5, rotY: 0.38, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });
            build3DBuilding({ id: 18, x: 7.7, z: 56.6, w: 11.5, d: 6.5, h: 6.5, rotY: 0.38, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });

            // 19. DAPUR PUTRI
            build3DBuilding({ id: 19, x: 33.8, z: 57.7, w: 14.0, d: 16.0, h: 5.0, rotY: 0.30, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 1 });
            build3DBuilding({ id: 19, x: 31.4, z: 70.2, w: 14.0, d: 7.0,  h: 5.4, rotY: 0.30, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 1 });
            build3DBuilding({ id: 19, x: 33.3, z: 82.9, w: 8.5,  d: 8.0,  h: 4.8, rotY: 0.30, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 1 });

            // 20. KANTIN PUTRI & MESS USTAZAH
            build3DBuilding({ id: 20, x: -2.1, z: 72.6, w: 13.0, d: 11.0, h: 5.5, rotY: 0.38, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });
            build3DBuilding({ id: 20, x: -0.4, z: 87.8, w: 8.5,  d: 5.0,  h: 4.5, rotY: -0.65, roofType: 'hipped', roofColor: ROOF_MID_GREY, floors: 1 });

            // 21. ASRAMA PUTRI (SELATAN)
            build3DBuilding({ id: 21, x: -17.2, z: 60.5, w: 15.5, d: 7.0, h: 6.5, rotY: 0.44, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });
            build3DBuilding({ id: 21, x: -21.6, z: 70.3, w: 15.5, d: 7.0, h: 6.5, rotY: 0.44, roofType: 'flat', roofColor: ROOF_LIGHT_GREY, floors: 2 });

            // 22. AULA STB
            build3DBuilding({ id: 22, x: -30.9, z: 54.1, w: 10.5, d: 11.5, h: 5.5, rotY: 0.44, roofType: 'hipped', roofColor: ROOF_BLUE_SLATE, floors: 1 });
        }"""

content = re.sub(r'function buildAll26Buildings\(\) \{.*?build3DBuilding\(\{ id: 22.*?\n        \}', buildings_code_new, content, flags=re.DOTALL)

# 4. Update buildGreenFieldsAndCourts with exact coordinates from Pemetaan.png
courts_code_new = """        function buildGreenFieldsAndCourts() {
            // 8. Lapangan Basket
            addCourtMesh(8, 26.2, -20.2, 10.0, 14.3, 0, 'basket');
            // 11. Lapangan Bola / Upacara
            addCourtMesh(11, 39.5, -1.7, 13.8, 24.4, 0.18, 'soccer');
            // 24. Lapangan Bulu Tangkis
            addCourtMesh(24, -24.1, -44.3, 11.0, 7.8, 0.22, 'net');
            // 25. Lapangan Asrama Putra
            addCourtMesh(25, -50.5, -17.0, 7.0, 12.0, 0, 'basket');
            // 26. Lapangan Voli
            addCourtMesh(26, -5.2, -74.0, 5.9, 9.6, 0.30, 'net');

            // 23. Lapangan Pesantren (L-Shaped Green Field matching Pemetaan.png)
            const fieldPts = [
                [-65, 18], [-28, 18], [-24, 6], [-8, 12],
                [-14, 40], [-45, 30], [-45, 52], [-65, 52]
            ];
            const fieldShape = createShapeFromCoords(fieldPts);
            const fieldGeo = new THREE.ExtrudeGeometry(fieldShape, { depth: 0.32, bevelEnabled: false });
            fieldGeo.rotateX(-Math.PI / 2);
            const fieldMesh = new THREE.Mesh(
                fieldGeo,
                new THREE.MeshLambertMaterial({ map: createStripedLawnTexture() })
            );
            fieldMesh.position.y = 0.25;
            fieldMesh.receiveShadow = true;
            fieldMesh.userData = { locationId: 23 };
            interactiveMeshes.push(fieldMesh);
            scene.add(fieldMesh);
        }"""

content = re.sub(r'function buildGreenFieldsAndCourts\(\) \{.*?scene\.add\(fieldMesh\);\n        \}', courts_code_new, content, flags=re.DOTALL)

# 5. Update buildYellowRoads with exact matching spine and spurs
roads_code_new = """        function buildYellowRoads() {
            const yellowHex = 0xf5d000;
            const borderHex = 0xd9b300;

            const segments = [
                // Main North-to-South Spine
                [[-8.9, -112.1], [-2.7, -100], [5, -85], [20, -60], [32, -40], [37, -23.3], [35, 0], [32, 17], [25, 45], [18, 68], [15, 82], [20, 98], [35, 111]],
                // Gate Triangle & Mosque Loop
                [[-8.9, -112.1], [-18, -83], [5, -85]],
                [[-18, -83], [-22, -78], [-24, -68], [-5, -61], [-6, -34]],
                // Spur East above Food Court (5)
                [[6, -48], [35, -43]],
                // Central Cross-Campus Road & Western Asrama Putra (9) Loop
                [[55, -20], [37, -23.3], [-6, -34], [-45, -34], [-58, -18], [-58, -4], [-50, 1], [-5, 2], [2, 8], [12, 10], [32, 17]],
                // Mess Ustad (12) Upper Branch
                [[2, 8], [12, -2], [25, -3], [37, -2]],
                // Tugu Globe (7) Triangle Connector
                [[35, -28], [42, -23.3], [35, -16]],
                // Spur East between Lapangan Bola (11) & Administrasi (14)
                [[32, 17], [52, 20]],
                // Spur East to Dapur Putri (19)
                [[22, 56], [35, 60]],
                // Spur West to Asrama Putri (18, 21) & Aula STB (22)
                [[18, 68], [8, 67], [-28, 48]]
            ];

            segments.forEach(pts => {
                buildRibbon3D(pts, 3.4, borderHex, 0.34, false, 0.25);
                buildRibbon3D(pts, 2.8, yellowHex, 0.39, false, 0.27);
            });
        }"""

content = re.sub(r'function buildYellowRoads\(\) \{.*?\}\);' + r'\n        \}', roads_code_new, content, flags=re.DOTALL)

# Write to index.html
open(INDEX_PATH, "w", encoding="utf-8").write(content)
print("Updated index.html with true Pemetaan coordinates!")

# Also update dist/index.html and denah_3d_offline.html
import base64
SAT_PATH = os.path.join(ROOT, "public", "textures", "satellite.jpg")
sat_bytes = open(SAT_PATH, "rb").read()
sat_b64 = "data:image/jpeg;base64," + base64.b64encode(sat_bytes).decode("ascii")
content_offline = content.replace('"public/textures/satellite.jpg"', f'"{sat_b64}"')
open(os.path.join(ROOT, "denah_3d_offline.html"), "w", encoding="utf-8").write(content_offline)
open(os.path.join(ROOT, "dist", "index.html"), "w", encoding="utf-8").write(content.replace("public/textures/", "textures/"))
print(f"Generated denah_3d_offline.html ({os.path.getsize(os.path.join(ROOT, 'denah_3d_offline.html')):,} bytes)")


