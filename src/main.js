import * as THREE from 'three';
import './style.css';

// ============================================================================
// 1. STATE, CONSTANTS & THEME PALETTES (SAMPLED FROM PREVIEW.WEBP - PREVIEW 4)
// ============================================================================
const ORIGIN = { lat: 5.399226, lng: 95.435794 };
const CAMPUS_DATA_URL = 'data/campus.json';

const STATE = {
  theme: 'light',       // 'light' | 'dark'
  mode: 'illustrated',  // 'illustrated' | 'hybrid' | 'satellite'
  trees: 'dense',       // 'none' | 'medium' | 'dense'
  view: 'north',        // 'north' | 'east' | 'top'
  tool: 'select',       // 'select' (Klik) | 'pan' (Hand Tool) | 'zoom' (Scale)
  showLabels: true,
  showNumbers: false,
  shadows: true,
  autoRotate: false,
  selectedId: null,
  activeHoverId: null,
};

// Exact color palettes sampled from preview.webp, preview (1).webp & preview (3).webp
const PALETTES = {
  light: {
    bg: 0xe3e7eb,
    ground: 0xf4f5f0,
    forestFloor: 0xdcebd9,
    slabWall: 0x888b90,
    slabSkirt: 0x60646a,
    boundaryRed: 0xef4444,
    roadAsphalt: 0x1e2024,
    roadShoulder: 0xd8dde2,
    roadYellow: 0xf5d000,
    roadYellowBorder: 0xc9a800,
    riverWater: 0x7b705d,
    riverBank: 0x5c5242,
    buildingWall: 0xf8fafc,
    buildingParapet: 0xe2e8f0,
    buildingFlatRoof: 0xcfd6de,
    buildingPitchedRoof: 0x788ba0,
    treeTrunk: 0x5c4230,
    palmTrunk: 0x6e533b,
    treeCanopyBase: 0xffffff, // multiplied by instanceColor
    treeShades: [0x2e7d32, 0x388e3c, 0x43a047, 0x1b5e20],
    palmFrond: 0x247a37,
    conifer: 0x1e6b34,
    dirLightColor: 0xfffef8,
    dirLightIntensity: 1.2,
    hemiSky: 0xffffff,
    hemiGround: 0xcbd5e1,
    hemiIntensity: 0.85,
    ambientIntensity: 0.35,
  },
  dark: {
    bg: 0x111518,
    ground: 0x2b3138,
    forestFloor: 0x203026,
    slabWall: 0x4b5059,
    slabSkirt: 0x25282e,
    boundaryRed: 0xdc2626,
    roadAsphalt: 0x14171b,
    roadShoulder: 0x47505c,
    roadYellow: 0xead013,
    roadYellowBorder: 0x7d6e09,
    riverWater: 0x5d5541,
    riverBank: 0x3f3a2c,
    buildingWall: 0xb4b8bc,
    buildingParapet: 0xcfd4d8,
    buildingFlatRoof: 0x9aa1a8,
    buildingPitchedRoof: 0x64748b,
    treeTrunk: 0x3d2c20,
    palmTrunk: 0x4a3828,
    treeCanopyBase: 0xffffff,
    treeShades: [0x27623c, 0x1f5231, 0x2f7347, 0x184327],
    palmFrond: 0x235c36,
    conifer: 0x1d4f2e,
    dirLightColor: 0xeef4ff,
    dirLightIntensity: 0.95,
    hemiSky: 0xdbeafe,
    hemiGround: 0x1e293b,
    hemiIntensity: 0.65,
    ambientIntensity: 0.3,
  },
};

let campusData = null;
let scene, camera, renderer, timer;
let dirLight, hemiLight, ambientLight;
let dioramaGroup, forestFloorGroup, buildingsGroup, roadsGroup, riversGroup, fieldsGroup, treesGroup, landmarksGroup;
let groundIllustratedMesh, groundSatelliteMesh, dioramaSlabMesh, slabSkirtMesh, boundaryRibbonMesh;
let raycaster, mouse;
let satelliteTexture = null;
let globeMesh = null;
let interactiveMeshes = [];
let labelElements = [];
let treeInstancedMeshes = [];
let roundCanopyMesh = null;

// Central material registry for instant Light/Dark theme switching
const MATS = {};

// Camera Orbit State
// View presets:
// - 'north' matches preview.webp & preview (3).webp
// - 'east' matches preview (1).webp, preview (2).webp & preview (4).webp
// - 'top' is top-down map inspection
const VIEW_PRESETS = {
  north: { theta: 0.06, phi: 0.88, radius: 690,  lookAt: new THREE.Vector3(-76, 0, 12) },
  east:  { theta: 2.38, phi: 0.93, radius: 660,  lookAt: new THREE.Vector3(-76, 0, 3) },
  top:   { theta: 0.0,  phi: 0.08, radius: 1190, lookAt: new THREE.Vector3(-76, 0, 10) },
};

const camState = {
  theta: VIEW_PRESETS.north.theta,
  phi: VIEW_PRESETS.north.phi,
  radius: VIEW_PRESETS.north.radius,
  target: VIEW_PRESETS.north.lookAt.clone(),
  targetTheta: VIEW_PRESETS.north.theta,
  targetPhi: VIEW_PRESETS.north.phi,
  targetRadius: VIEW_PRESETS.north.radius,
  targetLookAt: VIEW_PRESETS.north.lookAt.clone(),
  isDragging: false,
  isPanning: false,
  prevX: 0,
  prevY: 0,
  downX: 0,
  downY: 0,
};

// ============================================================================
// 2. GEOMETRY & ORIENTED BOUNDING BOX (OBB) HELPERS
// ============================================================================
function createShapeFromPoly(outerRing, holes = []) {
  const shape = new THREE.Shape();
  shape.moveTo(outerRing[0][0], -outerRing[0][1]);
  for (let i = 1; i < outerRing.length; i++) {
    shape.lineTo(outerRing[i][0], -outerRing[i][1]);
  }
  shape.closePath();

  holes.forEach((holeRing) => {
    if (!holeRing || holeRing.length < 3) return;
    const holePath = new THREE.Path();
    holePath.moveTo(holeRing[0][0], -holeRing[0][1]);
    for (let i = 1; i < holeRing.length; i++) {
      holePath.lineTo(holeRing[i][0], -holeRing[i][1]);
    }
    holePath.closePath();
    shape.holes.push(holePath);
  });
  return shape;
}

// Finds minimum-area oriented bounding box (OBB) in XZ plane for any polygon ring
function computeOBB(ring) {
  const candidateAngles = new Set();
  for (let i = 0; i < ring.length; i++) {
    const p1 = ring[i];
    const p2 = ring[(i + 1) % ring.length];
    const a = Math.atan2(p2[1] - p1[1], p2[0] - p1[0]);
    candidateAngles.add(a);
  }
  for (let deg = 0; deg < 180; deg += 3) {
    candidateAngles.add((deg * Math.PI) / 180);
  }

  let bestArea = Infinity;
  let best = null;

  candidateAngles.forEach((angle) => {
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    let minU = Infinity, maxU = -Infinity;
    let minV = Infinity, maxV = -Infinity;

    for (let i = 0; i < ring.length; i++) {
      const x = ring[i][0];
      const z = ring[i][1];
      const u = x * cos + z * sin;
      const v = -x * sin + z * cos;
      if (u < minU) minU = u;
      if (u > maxU) maxU = u;
      if (v < minV) minV = v;
      if (v > maxV) maxV = v;
    }

    const w = maxU - minU;
    const d = maxV - minV;
    const area = w * d;
    if (area < bestArea) {
      bestArea = area;
      const cu = (minU + maxU) / 2;
      const cv = (minV + maxV) / 2;
      const cx = cu * cos - cv * sin;
      const cz = cu * sin + cv * cos;
      best = { cx, cz, w, d, angle };
    }
  });

  // Normalize so d is always the longer axis (along local Z of court texture)
  if (best && best.w > best.d) {
    const tmp = best.w;
    best.w = best.d;
    best.d = tmp;
    best.angle += Math.PI / 2;
  }
  return best;
}

// Compute UV coordinates mapped to satellite bounding box after rotateX(-Math.PI/2)
function applySatelliteUVs(geometry, satMeta) {
  const pos = geometry.attributes.position;
  const uvs = new Float32Array(pos.count * 2);
  const w = satMeta.x1 - satMeta.x0;
  const h = satMeta.z1 - satMeta.z0;

  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const z = pos.getZ(i);
    const u = (x - satMeta.x0) / w;
    const v = 1.0 - (z - satMeta.z0) / h;
    uvs[i * 2] = u;
    uvs[i * 2 + 1] = v;
  }
  geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geometry.attributes.uv.needsUpdate = true;
}

// Compute UV coordinates aligned to a polygon's Oriented Bounding Box (for sports courts)
function applyOrientedBoxUVs(geometry, obb) {
  const pos = geometry.attributes.position;
  const uvs = new Float32Array(pos.count * 2);
  const cos = Math.cos(obb.angle);
  const sin = Math.sin(obb.angle);
  const w = Math.max(obb.w, 1);
  const d = Math.max(obb.d, 1);

  for (let i = 0; i < pos.count; i++) {
    const dx = pos.getX(i) - obb.cx;
    const dz = pos.getZ(i) - obb.cz;
    const localU = dx * cos + dz * sin;
    const localV = -dx * sin + dz * cos;
    uvs[i * 2] = THREE.MathUtils.clamp(localU / w + 0.5, 0.01, 0.99);
    uvs[i * 2 + 1] = THREE.MathUtils.clamp(localV / d + 0.5, 0.01, 0.99);
  }
  geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geometry.attributes.uv.needsUpdate = true;
}

// Merge multiple BufferGeometries into a single BufferGeometry (for volumetric trees)
function mergeSimpleGeometries(geometries) {
  let totalVerts = 0;
  let totalIndices = 0;
  geometries.forEach((g) => {
    totalVerts += g.attributes.position.count;
    totalIndices += g.index ? g.index.count : g.attributes.position.count;
  });

  const positions = new Float32Array(totalVerts * 3);
  const normals = new Float32Array(totalVerts * 3);
  const indices = new Uint32Array(totalIndices);

  let vertOffset = 0;
  let idxOffset = 0;

  geometries.forEach((g) => {
    const pos = g.attributes.position;
    const norm = g.attributes.normal;
    positions.set(pos.array, vertOffset * 3);
    if (norm) normals.set(norm.array, vertOffset * 3);

    if (g.index) {
      for (let i = 0; i < g.index.count; i++) {
        indices[idxOffset + i] = g.index.getX(i) + vertOffset;
      }
      idxOffset += g.index.count;
    } else {
      for (let i = 0; i < pos.count; i++) {
        indices[idxOffset + i] = vertOffset + i;
      }
      idxOffset += pos.count;
    }
    vertOffset += pos.count;
  });

  const merged = new THREE.BufferGeometry();
  merged.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  merged.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
  merged.setIndex(new THREE.BufferAttribute(indices, 1));
  return merged;
}

// ============================================================================
// 3. PROCEDURAL ARCHITECTURAL & COURT TEXTURES
// ============================================================================
function createCourtTexture(kind, isDark = false) {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');

  // Base turf / court colors matching preview.webp & preview (3).webp
  if (kind === 'soccer') {
    const c1 = isDark ? '#388540' : '#47a84b';
    const c2 = isDark ? '#327839' : '#3f9843';
    for (let i = 0; i < 12; i++) {
      ctx.fillStyle = i % 2 === 0 ? c1 : c2;
      ctx.fillRect(0, i * (512 / 12), 256, 512 / 12 + 1);
    }
  } else if (kind === 'basket') {
    ctx.fillStyle = isDark ? '#398643' : '#43a047';
    ctx.fillRect(0, 0, 256, 512);
  } else if (kind === 'volley') {
    ctx.fillStyle = isDark ? '#3b8945' : '#47a64c';
    ctx.fillRect(0, 0, 256, 512);
  } else {
    ctx.fillStyle = isDark ? '#3a8744' : '#45a249';
    ctx.fillRect(0, 0, 256, 512);
  }

  // Crisp white boundary & court markings
  ctx.strokeStyle = isDark ? 'rgba(240, 246, 252, 0.88)' : 'rgba(255, 255, 255, 0.95)';
  ctx.lineWidth = 6;
  ctx.strokeRect(16, 16, 224, 480);

  // Center line
  ctx.beginPath();
  ctx.moveTo(16, 256);
  ctx.lineTo(240, 256);
  ctx.stroke();

  if (kind === 'soccer' || kind === 'basket') {
    // Center circle
    ctx.beginPath();
    ctx.arc(128, 256, 44, 0, Math.PI * 2);
    ctx.stroke();

    // Penalty / Key boxes
    ctx.strokeRect(66, 16, 124, 78);
    ctx.strokeRect(66, 418, 124, 78);

    if (kind === 'soccer') {
      ctx.strokeRect(92, 16, 72, 34);
      ctx.strokeRect(92, 462, 72, 34);
    }
  } else if (kind === 'volley' || kind === 'badminton') {
    // Attack / service lines
    ctx.beginPath();
    ctx.moveTo(16, 176);
    ctx.lineTo(240, 176);
    ctx.moveTo(16, 336);
    ctx.lineTo(240, 336);
    ctx.stroke();
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function createGlobeTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = '#0284c7';
  ctx.fillRect(0, 0, 512, 256);

  ctx.fillStyle = '#22c55e';
  ctx.beginPath();
  ctx.ellipse(130, 90, 55, 40, 0.2, 0, Math.PI * 2);
  ctx.ellipse(170, 170, 45, 55, -0.3, 0, Math.PI * 2);
  ctx.ellipse(320, 80, 80, 45, -0.1, 0, Math.PI * 2);
  ctx.ellipse(340, 140, 60, 50, 0.1, 0, Math.PI * 2);
  ctx.ellipse(400, 180, 40, 30, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.28)';
  ctx.lineWidth = 2;
  for (let x = 0; x < 512; x += 64) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 256);
    ctx.stroke();
  }
  for (let y = 0; y < 256; y += 42) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(512, y);
    ctx.stroke();
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

// ============================================================================
// 4. THREE.JS SCENE, CAMERA, RENDERER & MATERIALS
// ============================================================================
function initMaterials() {
  const p = PALETTES[STATE.theme];

  MATS.ground = new THREE.MeshStandardMaterial({ color: p.ground, roughness: 0.95, metalness: 0.02 });
  MATS.forestFloor = new THREE.MeshStandardMaterial({ color: p.forestFloor, roughness: 0.96, metalness: 0.0 });
  MATS.slabWall = new THREE.MeshStandardMaterial({ color: p.slabWall, roughness: 0.85, metalness: 0.08 });
  MATS.slabSkirt = new THREE.MeshStandardMaterial({ color: p.slabSkirt, roughness: 0.9, metalness: 0.05 });
  MATS.boundaryRed = new THREE.MeshStandardMaterial({ color: p.boundaryRed, roughness: 0.45, metalness: 0.1 });

  MATS.roadAsphalt = new THREE.MeshStandardMaterial({ color: p.roadAsphalt, roughness: 0.88, metalness: 0.05 });
  MATS.roadShoulder = new THREE.MeshStandardMaterial({ color: p.roadShoulder, roughness: 0.85 });
  MATS.roadYellow = new THREE.MeshStandardMaterial({ color: p.roadYellow, roughness: 0.6, metalness: 0.08 });
  MATS.roadYellowBorder = new THREE.MeshStandardMaterial({ color: p.roadYellowBorder, roughness: 0.75 });

  MATS.riverWater = new THREE.MeshStandardMaterial({ color: p.riverWater, roughness: 0.78, metalness: 0.12 });
  MATS.riverBank = new THREE.MeshStandardMaterial({ color: p.riverBank, roughness: 0.9 });

  MATS.buildingWall = new THREE.MeshStandardMaterial({ color: p.buildingWall, roughness: 0.72, metalness: 0.05 });
  MATS.buildingParapet = new THREE.MeshStandardMaterial({ color: p.buildingParapet, roughness: 0.76, metalness: 0.05 });
  MATS.buildingFlatRoof = new THREE.MeshStandardMaterial({ color: p.buildingFlatRoof, roughness: 0.86 });
  MATS.buildingPitchedRoof = new THREE.MeshStandardMaterial({ color: p.buildingPitchedRoof, roughness: 0.72, metalness: 0.08 });

  MATS.treeTrunk = new THREE.MeshStandardMaterial({ color: p.treeTrunk, roughness: 0.92 });
  MATS.palmTrunk = new THREE.MeshStandardMaterial({ color: p.palmTrunk, roughness: 0.92 });
  MATS.treeCanopy = new THREE.MeshStandardMaterial({ color: p.treeCanopyBase, roughness: 0.82, metalness: 0.02 });
  MATS.palmFrond = new THREE.MeshStandardMaterial({ color: p.palmFrond, roughness: 0.78, side: THREE.DoubleSide });
  MATS.conifer = new THREE.MeshStandardMaterial({ color: p.conifer, roughness: 0.84 });

  MATS.satellite = new THREE.MeshStandardMaterial({
    map: satelliteTexture,
    color: 0xffffff,
    roughness: 0.88,
    metalness: 0.02,
  });
}

function initScene() {
  const canvas = document.getElementById('scene');
  const p = PALETTES[STATE.theme];

  scene = new THREE.Scene();
  scene.background = new THREE.Color(p.bg);

  camera = new THREE.PerspectiveCamera(32, window.innerWidth / window.innerHeight, 5, 3200);
  updateCameraPosition(true);

  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    powerPreference: 'high-performance',
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.04;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  if (satelliteTexture) {
    satelliteTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
    satelliteTexture.needsUpdate = true;
  }

  initMaterials();

  // Balanced architectural sun & sky illumination
  hemiLight = new THREE.HemisphereLight(p.hemiSky, p.hemiGround, p.hemiIntensity);
  hemiLight.position.set(0, 450, 0);
  scene.add(hemiLight);

  dirLight = new THREE.DirectionalLight(p.dirLightColor, p.dirLightIntensity);
  dirLight.position.set(-240, 440, 210);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 2048;
  dirLight.shadow.mapSize.height = 2048;
  dirLight.shadow.camera.near = 50;
  dirLight.shadow.camera.far = 1100;
  const d = 420;
  dirLight.shadow.camera.left = -d;
  dirLight.shadow.camera.right = d;
  dirLight.shadow.camera.top = d;
  dirLight.shadow.camera.bottom = -d;
  dirLight.shadow.bias = -0.0004;
  scene.add(dirLight);

  ambientLight = new THREE.AmbientLight(0xffffff, p.ambientIntensity);
  scene.add(ambientLight);

  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2(-999, -999);
  timer = new THREE.Timer();

  // Scene hierarchy groups
  dioramaGroup = new THREE.Group();
  forestFloorGroup = new THREE.Group();
  riversGroup = new THREE.Group();
  roadsGroup = new THREE.Group();
  fieldsGroup = new THREE.Group();
  buildingsGroup = new THREE.Group();
  landmarksGroup = new THREE.Group();
  treesGroup = new THREE.Group();

  scene.add(dioramaGroup);
  scene.add(forestFloorGroup);
  scene.add(riversGroup);
  scene.add(roadsGroup);
  scene.add(fieldsGroup);
  scene.add(buildingsGroup);
  scene.add(landmarksGroup);
  scene.add(treesGroup);

  initControls();
  window.addEventListener('resize', onWindowResize);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  updateFloatingLabels();
}

// ============================================================================
// 5. DIORAMA SLAB, SATELLITE SURFACE, ROADS, RIVERS & FIELDS
// ============================================================================
function buildDioramaBase() {
  const boundary = campusData.boundary;
  const shape = createShapeFromPoly(boundary);

  // 1. Thick Beveled Architectural Diorama Pedestal Slab
  // Top of slab sits at y = -0.6 so it never z-fights with ground surface at y = 0.0
  const slabDepth = 22;
  const slabGeo = new THREE.ExtrudeGeometry(shape, {
    depth: slabDepth,
    bevelEnabled: true,
    bevelThickness: 1.6,
    bevelSize: 2.0,
    bevelSegments: 2,
  });
  slabGeo.rotateX(-Math.PI / 2);
  slabGeo.computeVertexNormals();

  dioramaSlabMesh = new THREE.Mesh(slabGeo, MATS.slabWall);
  dioramaSlabMesh.position.y = -(slabDepth + 2.2);
  dioramaSlabMesh.receiveShadow = true;
  dioramaSlabMesh.castShadow = true;
  dioramaGroup.add(dioramaSlabMesh);

  // Bottom dark plinth skirt
  const skirtGeo = new THREE.ExtrudeGeometry(shape, { depth: 5.5, bevelEnabled: false });
  skirtGeo.rotateX(-Math.PI / 2);
  slabSkirtMesh = new THREE.Mesh(skirtGeo, MATS.slabSkirt);
  slabSkirtMesh.position.y = -(slabDepth + 7.2);
  dioramaGroup.add(slabSkirtMesh);

  // 2. Illustrated Top Campus Ground (Top surface at y = 0.00)
  const topGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.8, bevelEnabled: false });
  topGeo.rotateX(-Math.PI / 2);
  groundIllustratedMesh = new THREE.Mesh(topGeo, MATS.ground);
  groundIllustratedMesh.position.y = -0.8;
  groundIllustratedMesh.receiveShadow = true;
  dioramaGroup.add(groundIllustratedMesh);

  // 3. Real Satellite Orthophoto Surface (Top surface at y = +0.04)
  const satGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.84, bevelEnabled: false });
  satGeo.rotateX(-Math.PI / 2);
  applySatelliteUVs(satGeo, campusData.satellite);

  groundSatelliteMesh = new THREE.Mesh(satGeo, MATS.satellite);
  groundSatelliteMesh.position.y = -0.8;
  groundSatelliteMesh.receiveShadow = true;
  groundSatelliteMesh.visible = STATE.mode !== 'illustrated';
  dioramaGroup.add(groundSatelliteMesh);

  // 4. Forest Woodland Floor Tint Polygons (Top surface at y = +0.08)
  if (campusData.forest) {
    campusData.forest.forEach((fPoly) => {
      const fShape = createShapeFromPoly(fPoly.outer, fPoly.holes);
      const fGeo = new THREE.ExtrudeGeometry(fShape, { depth: 0.08, bevelEnabled: false });
      fGeo.rotateX(-Math.PI / 2);
      const fMesh = new THREE.Mesh(fGeo, MATS.forestFloor);
      fMesh.position.y = 0.0;
      fMesh.receiveShadow = true;
      forestFloorGroup.add(fMesh);
    });
  }

  // 5. Red Outer Campus Boundary Line (#ef4444)
  buildBoundaryRibbon(boundary);

  // 6. Black Perimeter Asphalt Road + White Shoulders
  buildPerimeterAsphaltRoad();
}

function buildBoundaryRibbon(pts) {
  const group = new THREE.Group();
  const width = 2.4;
  const height = 0.55;

  for (let i = 0; i < pts.length; i++) {
    const p1 = pts[i];
    const p2 = pts[(i + 1) % pts.length];
    const dx = p2[0] - p1[0];
    const dz = p2[1] - p1[1];
    const dist = Math.hypot(dx, dz);
    if (dist < 0.2) continue;

    const segment = new THREE.Mesh(new THREE.BoxGeometry(width, height, dist + width * 0.2), MATS.boundaryRed);
    segment.position.set((p1[0] + p2[0]) / 2, 0.35, (p1[1] + p2[1]) / 2);
    segment.rotation.y = Math.atan2(dx, dz);
    segment.receiveShadow = true;
    group.add(segment);

    const corner = new THREE.Mesh(new THREE.CylinderGeometry(width * 0.5, width * 0.5, height, 12), MATS.boundaryRed);
    corner.position.set(p1[0], 0.35, p1[1]);
    corner.receiveShadow = true;
    group.add(corner);
  }
  boundaryRibbonMesh = group;
  dioramaGroup.add(group);
}

function buildPerimeterAsphaltRoad() {
  if (!campusData.roadsMain) return;

  // Shoulder layer: top surface at y = +0.22
  campusData.roadsMain.forEach((item) => {
    const shoulderShape = createShapeFromPoly(item.outer, item.holes);
    const shoulderGeo = new THREE.ExtrudeGeometry(shoulderShape, { depth: 0.16, bevelEnabled: false });
    shoulderGeo.rotateX(-Math.PI / 2);
    const shoulderMesh = new THREE.Mesh(shoulderGeo, MATS.roadShoulder);
    shoulderMesh.position.y = 0.06;
    shoulderMesh.receiveShadow = true;
    roadsGroup.add(shoulderMesh);
  });

  // Black asphalt core layer: top surface at y = +0.34
  if (campusData.roadsCore) {
    campusData.roadsCore.forEach((item) => {
      const roadShape = createShapeFromPoly(item.outer, item.holes);
      const roadGeo = new THREE.ExtrudeGeometry(roadShape, { depth: 0.24, bevelEnabled: false });
      roadGeo.rotateX(-Math.PI / 2);
      const roadMesh = new THREE.Mesh(roadGeo, MATS.roadAsphalt);
      roadMesh.position.y = 0.10;
      roadMesh.receiveShadow = true;
      roadsGroup.add(roadMesh);
    });
  }
}

function buildRivers() {
  if (!campusData.rivers) return;

  campusData.rivers.forEach((item) => {
    const shape = createShapeFromPoly(item.outer, item.holes);

    // River bank: top surface at y = +0.16
    const bankGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.12, bevelEnabled: false });
    bankGeo.rotateX(-Math.PI / 2);
    const bankMesh = new THREE.Mesh(bankGeo, MATS.riverBank);
    bankMesh.position.y = 0.04;
    bankMesh.receiveShadow = true;
    riversGroup.add(bankMesh);

    // River water surface: top surface at y = +0.24
    const riverGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.18, bevelEnabled: false });
    riverGeo.rotateX(-Math.PI / 2);
    const riverMesh = new THREE.Mesh(riverGeo, MATS.riverWater);
    riverMesh.position.y = 0.06;
    riverMesh.receiveShadow = true;
    riversGroup.add(riverMesh);
  });
}

function buildYellowRoads() {
  if (!campusData.roadsInternal) return;

  campusData.roadsInternal.forEach((item) => {
    const shape = createShapeFromPoly(item.outer, item.holes);

    // Subtle border: top surface at y = +0.30
    const borderGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.20, bevelEnabled: false });
    borderGeo.rotateX(-Math.PI / 2);
    const borderMesh = new THREE.Mesh(borderGeo, MATS.roadYellowBorder);
    borderMesh.position.y = 0.10;
    borderMesh.receiveShadow = true;
    roadsGroup.add(borderMesh);

    // Vivid yellow internal road: top surface at y = +0.40
    const roadGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.28, bevelEnabled: false });
    roadGeo.rotateX(-Math.PI / 2);
    const roadMesh = new THREE.Mesh(roadGeo, MATS.roadYellow);
    roadMesh.position.y = 0.12;
    roadMesh.receiveShadow = true;
    roadsGroup.add(roadMesh);
  });
}

function buildFields() {
  if (!campusData.fields) return;

  campusData.fields.forEach((item) => {
    const locId = item.loc;
    const locMeta = campusData.locations.find((l) => l.id === locId) || {};
    const courtKind = locMeta.court || (locId === 23 ? 'soccer' : 'lawn');

    const obb = computeOBB(item.outer);
    const shape = createShapeFromPoly(item.outer, item.holes);
    const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.34, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2);
    applyOrientedBoxUVs(geo, obb);

    const texLight = createCourtTexture(courtKind, false);
    const texDark = createCourtTexture(courtKind, true);

    const mat = new THREE.MeshStandardMaterial({
      map: STATE.theme === 'dark' ? texDark : texLight,
      roughness: 0.85,
      metalness: 0.02,
    });
    mat.userData = { texLight, texDark };

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = 0.12; // Top surface at y = +0.46
    mesh.receiveShadow = true;
    mesh.userData = { locationId: locId };
    interactiveMeshes.push(mesh);
    fieldsGroup.add(mesh);

    // Add 3D court equipment (soccer goals, basketball hoops, nets)
    buildCourtEquipment(obb, courtKind, 0.46);
  });
}

function buildCourtEquipment(obb, kind, baseY) {
  const equipGroup = new THREE.Group();
  equipGroup.position.set(obb.cx, baseY, obb.cz);
  equipGroup.rotation.y = -obb.angle;

  const postMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4, metalness: 0.3 });
  const halfD = obb.d * 0.44;

  if (kind === 'soccer') {
    [-halfD, halfD].forEach((zPos) => {
      const goal = new THREE.Group();
      goal.position.set(0, 0, zPos);
      const p1 = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.4, 8), postMat);
      p1.position.set(-3.2, 1.2, 0);
      const p2 = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.4, 8), postMat);
      p2.position.set(3.2, 1.2, 0);
      const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 6.6, 8), postMat);
      bar.rotation.z = Math.PI / 2;
      bar.position.set(0, 2.4, 0);
      goal.add(p1, p2, bar);
      equipGroup.add(goal);
    });
  } else if (kind === 'basket') {
    [-halfD, halfD].forEach((zPos) => {
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 2.8, 8), postMat);
      pole.position.set(0, 1.4, zPos);
      const board = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.0, 0.1), postMat);
      board.position.set(0, 2.6, zPos + (zPos > 0 ? -0.3 : 0.3));
      equipGroup.add(pole, board);
    });
  } else if (kind === 'volley' || kind === 'badminton') {
    const netW = obb.w * 0.82;
    const net = new THREE.Mesh(
      new THREE.BoxGeometry(netW, 0.9, 0.08),
      new THREE.MeshStandardMaterial({ color: 0xf8fafc, transparent: true, opacity: 0.75 })
    );
    net.position.set(0, 1.1, 0);
    equipGroup.add(net);
  }

  fieldsGroup.add(equipGroup);
}

// ============================================================================
// 6. 3D ARCHITECTURAL BUILDINGS (EXACT POLYGONS FROM PEMETAAN.PNG)
// ============================================================================
function buildBuildings() {
  if (!campusData.buildings) return;

  campusData.buildings.forEach((item) => {
    const locId = item.loc;
    const locMeta = campusData.locations.find((l) => l.id === locId) || {
      name: 'Gedung',
      floors: 2,
      roof: 'flat',
    };

    const floors = locMeta.floors || 2;
    const height = floors * 4.2 + 1.2;
    const shape = createShapeFromPoly(item.outer, item.holes);
    const obb = computeOBB(item.outer);

    const buildingGroup = new THREE.Group();
    buildingGroup.userData = { locationId: locId };

    // Clean architectural massing extruded directly from the exact polygon
    const wallGeo = new THREE.ExtrudeGeometry(shape, {
      depth: height,
      bevelEnabled: true,
      bevelThickness: 0.15,
      bevelSize: 0.12,
      bevelSegments: 1,
    });
    wallGeo.rotateX(-Math.PI / 2);

    // Note: in ExtrudeGeometry, group 0 is caps (top/bottom) and group 1 is side walls
    const bodyMesh = new THREE.Mesh(wallGeo, [MATS.buildingParapet, MATS.buildingWall]);
    bodyMesh.position.y = 0.35;
    bodyMesh.castShadow = true;
    bodyMesh.receiveShadow = true;
    bodyMesh.userData = { locationId: locId };
    interactiveMeshes.push(bodyMesh);
    buildingGroup.add(bodyMesh);

    // Subtle horizontal floor shadow band rings on multi-story buildings
    for (let f = 1; f < floors; f++) {
      const bandGeo = new THREE.ExtrudeGeometry(shape, {
        depth: 0.22,
        bevelEnabled: true,
        bevelThickness: 0.05,
        bevelSize: 0.18,
        bevelSegments: 1,
      });
      bandGeo.rotateX(-Math.PI / 2);
      const bandMesh = new THREE.Mesh(bandGeo, MATS.buildingParapet);
      bandMesh.position.y = 0.35 + f * 4.2;
      buildingGroup.add(bandMesh);
    }

    const cx = item.centroid[0];
    const cz = item.centroid[1];
    const roofY = height + 0.35;

    if (locMeta.roof === 'mosque') {
      // 4. Masjid Baburrayyan: Flat Parapet + Emerald Dome + Crescent + Minaret
      buildFlatParapetRoof(buildingGroup, shape, roofY);
      buildMosqueRoof(buildingGroup, cx, cz, roofY + 0.6);
    } else if (locMeta.roof === 'dome') {
      // 17. Musalla Putri: Flat Parapet + Emerald Dome
      buildFlatParapetRoof(buildingGroup, shape, roofY);
      buildDomeRoof(buildingGroup, cx, cz, roofY + 0.5);
    } else if (locMeta.roof === 'gable' || locMeta.roof === 'hip') {
      // Pitched / Hipped Roof aligned to the building's exact OBB orientation
      buildFlatParapetRoof(buildingGroup, shape, roofY);
      buildOrientedHippedRoof(buildingGroup, obb, roofY + 0.4);
    } else {
      // Crisp Architectural Flat Roof with Raised Parapet Rim
      buildFlatParapetRoof(buildingGroup, shape, roofY);
    }

    buildingsGroup.add(buildingGroup);
  });

  // 1. Gerbang Utama 3D Gate Landmark
  buildMainEntranceGate();

  // 7. Tugu Globe Landmark
  buildGlobeMonument();
}

function buildFlatParapetRoof(group, shape, roofY) {
  // Raised outer parapet rim
  const parapetGeo = new THREE.ExtrudeGeometry(shape, {
    depth: 0.85,
    bevelEnabled: true,
    bevelThickness: 0.18,
    bevelSize: 0.24,
    bevelSegments: 1,
  });
  parapetGeo.rotateX(-Math.PI / 2);
  const parapetMesh = new THREE.Mesh(parapetGeo, MATS.buildingParapet);
  parapetMesh.position.y = roofY;
  parapetMesh.castShadow = true;
  parapetMesh.receiveShadow = true;
  group.add(parapetMesh);

  // Inner recessed flat roof deck
  const roofGeo = new THREE.ExtrudeGeometry(shape, { depth: 0.92, bevelEnabled: false });
  roofGeo.rotateX(-Math.PI / 2);
  const roofMesh = new THREE.Mesh(roofGeo, MATS.buildingFlatRoof);
  roofMesh.position.y = roofY;
  roofMesh.receiveShadow = true;
  group.add(roofMesh);
}

function buildOrientedHippedRoof(group, obb, roofY) {
  const roofHeight = Math.min(3.8, Math.max(2.2, Math.min(obb.w, obb.d) * 0.24));
  const coneGeo = new THREE.ConeGeometry(1.0, roofHeight, 4);
  coneGeo.rotateY(Math.PI / 4); // Align 4-sided pyramid base with X and Z axes

  const roofMesh = new THREE.Mesh(coneGeo, MATS.buildingPitchedRoof);
  roofMesh.position.set(obb.cx, roofY + roofHeight * 0.5, obb.cz);
  roofMesh.rotation.y = -obb.angle;
  // Scale pyramid base to match exact OBB width & depth (with slight architectural overhang)
  const scaleX = (obb.w * 0.94) / Math.SQRT2;
  const scaleZ = (obb.d * 0.94) / Math.SQRT2;
  roofMesh.scale.set(scaleX, 1, scaleZ);
  roofMesh.castShadow = true;
  roofMesh.receiveShadow = true;
  group.add(roofMesh);
}

function buildDomeRoof(group, cx, cz, roofY) {
  const domeMat = new THREE.MeshStandardMaterial({
    color: 0x1e8e45,
    roughness: 0.35,
    metalness: 0.25,
  });
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(3.8, 4.0, 1.1, 24), MATS.buildingWall);
  drum.position.set(cx, roofY + 0.55, cz);
  drum.castShadow = true;
  group.add(drum);

  const dome = new THREE.Mesh(new THREE.SphereGeometry(3.7, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), domeMat);
  dome.position.set(cx, roofY + 1.1, cz);
  dome.castShadow = true;
  group.add(dome);

  const finial = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.2, 1.5, 8),
    new THREE.MeshStandardMaterial({ color: 0xfacc15, metalness: 0.8, roughness: 0.2 })
  );
  finial.position.set(cx, roofY + 5.2, cz);
  group.add(finial);
}

function buildMosqueRoof(group, cx, cz, roofY) {
  const domeMat = new THREE.MeshStandardMaterial({
    color: 0x1b843f,
    roughness: 0.32,
    metalness: 0.28,
  });
  const goldMat = new THREE.MeshStandardMaterial({
    color: 0xfacc15,
    metalness: 0.85,
    roughness: 0.2,
  });

  // Octagonal / circular drum
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(6.4, 6.8, 1.8, 24), MATS.buildingWall);
  drum.position.set(cx, roofY + 0.9, cz);
  drum.castShadow = true;
  group.add(drum);

  // Main emerald dome
  const dome = new THREE.Mesh(new THREE.SphereGeometry(6.2, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2), domeMat);
  dome.position.set(cx, roofY + 1.8, cz);
  dome.castShadow = true;
  group.add(dome);

  // Finial spire & crescent
  const finial = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.28, 2.6, 8), goldMat);
  finial.position.set(cx, roofY + 8.9, cz);
  group.add(finial);

  const crescent = new THREE.Mesh(new THREE.TorusGeometry(0.65, 0.12, 8, 18, Math.PI * 1.5), goldMat);
  crescent.position.set(cx, roofY + 10.3, cz);
  crescent.rotation.y = Math.PI / 4;
  group.add(crescent);

  // Corner Minaret Tower
  const minaret = new THREE.Group();
  const minBase = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.85, 18, 16), MATS.buildingWall);
  minBase.position.y = 9;
  minBase.castShadow = true;
  minaret.add(minBase);

  const balcony = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 1.6, 1.3, 16), MATS.buildingParapet);
  balcony.position.y = 18.6;
  balcony.castShadow = true;
  minaret.add(balcony);

  const spire = new THREE.Mesh(new THREE.ConeGeometry(1.45, 4.2, 16), domeMat);
  spire.position.y = 21.3;
  spire.castShadow = true;
  minaret.add(spire);

  minaret.position.set(cx + 9.0, 0.35, cz - 8.5);
  group.add(minaret);
}

function buildMainEntranceGate() {
  const loc = campusData.locations.find((l) => l.id === 1);
  if (!loc) return;

  const group = new THREE.Group();
  group.position.set(loc.x, 0.35, loc.z);

  const archMat = new THREE.MeshStandardMaterial({ color: 0x1b843f, roughness: 0.4, metalness: 0.2 });

  const p1 = new THREE.Mesh(new THREE.BoxGeometry(1.8, 6.5, 1.8), MATS.buildingWall);
  p1.position.set(-4.5, 3.25, 0);
  p1.castShadow = true;
  group.add(p1);

  const p2 = new THREE.Mesh(new THREE.BoxGeometry(1.8, 6.5, 1.8), MATS.buildingWall);
  p2.position.set(4.5, 3.25, 0);
  p2.castShadow = true;
  group.add(p2);

  const beam = new THREE.Mesh(new THREE.BoxGeometry(11.5, 1.8, 2.2), archMat);
  beam.position.set(0, 6.6, 0);
  beam.castShadow = true;
  group.add(beam);

  group.userData = { locationId: 1 };
  interactiveMeshes.push(beam);
  landmarksGroup.add(group);
}

function buildGlobeMonument() {
  const loc = campusData.locations.find((l) => l.id === 7);
  if (!loc) return;

  // Render exact blue triangular island from Pemetaan.png if available
  if (campusData.globe && campusData.globe.length > 0) {
    campusData.globe.forEach((gPoly) => {
      const shape = createShapeFromPoly(gPoly.outer, gPoly.holes);
      const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.42, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.1 });
      geo.rotateX(-Math.PI / 2);
      const plazaMesh = new THREE.Mesh(
        geo,
        new THREE.MeshStandardMaterial({ color: 0x2998e2, roughness: 0.45, metalness: 0.1 })
      );
      plazaMesh.position.y = 0.12;
      plazaMesh.receiveShadow = true;
      landmarksGroup.add(plazaMesh);
    });
  }

  const group = new THREE.Group();
  group.position.set(loc.x, 0.45, loc.z);

  const ped = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 2.0, 2.8, 8), MATS.buildingWall);
  ped.position.y = 1.4;
  ped.castShadow = true;
  group.add(ped);

  const globeTex = createGlobeTexture();
  const globeMat = new THREE.MeshStandardMaterial({
    map: globeTex,
    roughness: 0.38,
    metalness: 0.18,
  });
  globeMesh = new THREE.Mesh(new THREE.SphereGeometry(2.2, 28, 20), globeMat);
  globeMesh.position.y = 4.1;
  globeMesh.castShadow = true;
  globeMesh.userData = { locationId: 7 };
  interactiveMeshes.push(globeMesh);
  group.add(globeMesh);

  group.userData = { locationId: 7 };
  landmarksGroup.add(group);
}

// ============================================================================
// 7. SATELLITE-DERIVED FOREST & VEGETATION (2,230 TREES AT 60 FPS)
// ============================================================================
function buildVegetation() {
  if (!campusData.trees) return;

  // Deterministic ordering so that slicing 42% for 'medium' mode preserves spatial distribution
  const roundTrees = [];
  const palmTrees = [];
  const coniferTrees = [];

  campusData.trees.forEach((t) => {
    const [, , kind] = t;
    if (kind === 1) palmTrees.push(t);
    else if (kind === 2) coniferTrees.push(t);
    else roundTrees.push(t);
  });

  buildInstancedRoundTrees(roundTrees);
  buildInstancedPalmTrees(palmTrees);
  buildInstancedConiferTrees(coniferTrees);

  applyTreeDensityMode();
}

function buildInstancedRoundTrees(trees) {
  const trunkGeo = new THREE.CylinderGeometry(0.32, 0.52, 3.0, 7);
  trunkGeo.translate(0, 1.5, 0);

  // Volumetric multi-puff tree crown matching preview.webp
  const puffMain = new THREE.IcosahedronGeometry(2.5, 2);
  puffMain.translate(0, 4.6, 0);
  const puff1 = new THREE.IcosahedronGeometry(1.85, 1);
  puff1.translate(1.2, 4.0, 0.8);
  const puff2 = new THREE.IcosahedronGeometry(1.8, 1);
  puff2.translate(-1.1, 4.1, 0.7);
  const puff3 = new THREE.IcosahedronGeometry(1.75, 1);
  puff3.translate(0.1, 4.2, -1.2);
  const canopyGeo = mergeSimpleGeometries([puffMain, puff1, puff2, puff3]);

  const trunkInst = new THREE.InstancedMesh(trunkGeo, MATS.treeTrunk, trees.length);
  const canopyInst = new THREE.InstancedMesh(canopyGeo, MATS.treeCanopy, trees.length);

  trunkInst.castShadow = true;
  trunkInst.receiveShadow = true;
  canopyInst.castShadow = true;
  canopyInst.receiveShadow = true;

  const dummy = new THREE.Object3D();
  trees.forEach((t, i) => {
    const [x, z, , scale, cls] = t;
    // Forest trees (cls === 2) are fuller and slightly taller
    const s = cls === 2 ? scale * 1.06 : scale * 0.95;
    dummy.position.set(x, 0.15, z);
    dummy.scale.set(s, s, s);
    dummy.rotation.y = (x * 13.7 + z * 17.3) % (Math.PI * 2);
    dummy.updateMatrix();

    trunkInst.setMatrixAt(i, dummy.matrix);
    canopyInst.setMatrixAt(i, dummy.matrix);
  });

  trunkInst.instanceMatrix.needsUpdate = true;
  canopyInst.instanceMatrix.needsUpdate = true;

  trunkInst.userData = { totalCount: trees.length };
  canopyInst.userData = { totalCount: trees.length, treesData: trees };
  roundCanopyMesh = canopyInst;

  updateTreeCanopyColors();

  treeInstancedMeshes.push(trunkInst, canopyInst);
  treesGroup.add(trunkInst, canopyInst);
}

function updateTreeCanopyColors() {
  if (!roundCanopyMesh) return;
  const shades = PALETTES[STATE.theme].treeShades.map((hex) => new THREE.Color(hex));
  const total = roundCanopyMesh.userData.totalCount;
  for (let i = 0; i < total; i++) {
    roundCanopyMesh.setColorAt(i, shades[i % shades.length]);
  }
  if (roundCanopyMesh.instanceColor) roundCanopyMesh.instanceColor.needsUpdate = true;
}

function buildInstancedPalmTrees(trees) {
  const trunkGeo = new THREE.CylinderGeometry(0.22, 0.38, 6.4, 7);
  trunkGeo.translate(0, 3.2, 0);

  // Multi-frond tropical coconut palm crown
  const fronds = [];
  const numFronds = 6;
  for (let f = 0; f < numFronds; f++) {
    const angle = (f * Math.PI * 2) / numFronds;
    const fGeo = new THREE.ConeGeometry(1.1, 3.4, 4);
    fGeo.scale(0.55, 1.0, 0.15);
    fGeo.rotateX(Math.PI * 0.38);
    fGeo.translate(0, 6.2, 1.3);
    fGeo.rotateY(angle);
    fronds.push(fGeo);
  }
  const frondGeo = mergeSimpleGeometries(fronds);

  const trunkInst = new THREE.InstancedMesh(trunkGeo, MATS.palmTrunk, trees.length);
  const frondInst = new THREE.InstancedMesh(frondGeo, MATS.palmFrond, trees.length);

  trunkInst.castShadow = true;
  frondInst.castShadow = true;
  frondInst.receiveShadow = true;

  const dummy = new THREE.Object3D();
  trees.forEach((t, i) => {
    const [x, z, , scale] = t;
    dummy.position.set(x, 0.15, z);
    dummy.scale.set(scale, scale * 1.1, scale);
    dummy.rotation.y = (x * 7.1 + z * 3.7) % (Math.PI * 2);
    dummy.updateMatrix();

    trunkInst.setMatrixAt(i, dummy.matrix);
    frondInst.setMatrixAt(i, dummy.matrix);
  });

  trunkInst.instanceMatrix.needsUpdate = true;
  frondInst.instanceMatrix.needsUpdate = true;

  trunkInst.userData = { totalCount: trees.length };
  frondInst.userData = { totalCount: trees.length };

  treeInstancedMeshes.push(trunkInst, frondInst);
  treesGroup.add(trunkInst, frondInst);
}

function buildInstancedConiferTrees(trees) {
  const tier1 = new THREE.ConeGeometry(2.2, 4.2, 7);
  tier1.translate(0, 3.0, 0);
  const tier2 = new THREE.ConeGeometry(1.6, 3.4, 7);
  tier2.translate(0, 5.0, 0);
  const geo = mergeSimpleGeometries([tier1, tier2]);

  const inst = new THREE.InstancedMesh(geo, MATS.conifer, trees.length);
  inst.castShadow = true;
  inst.receiveShadow = true;

  const dummy = new THREE.Object3D();
  trees.forEach((t, i) => {
    const [x, z, , scale] = t;
    dummy.position.set(x, 0.15, z);
    dummy.scale.set(scale, scale, scale);
    dummy.rotation.y = (x + z) % (Math.PI * 2);
    dummy.updateMatrix();
    inst.setMatrixAt(i, dummy.matrix);
  });
  inst.instanceMatrix.needsUpdate = true;
  inst.userData = { totalCount: trees.length };

  treeInstancedMeshes.push(inst);
  treesGroup.add(inst);
}

function applyTreeDensityMode() {
  if (STATE.mode === 'satellite' || STATE.trees === 'none') {
    treesGroup.visible = false;
    forestFloorGroup.visible = false;
    return;
  }

  treesGroup.visible = true;
  forestFloorGroup.visible = STATE.mode === 'illustrated';

  const ratio = STATE.trees === 'dense' ? 1.0 : 0.42;
  treeInstancedMeshes.forEach((mesh) => {
    mesh.count = Math.floor(mesh.userData.totalCount * ratio);
  });
}

// ============================================================================
// 8. FLOATING 3D LABELS SYSTEM (PRIMARY 1-26 + MULTI-BUILDING SUB-LABELS)
// ============================================================================
function initFloatingLabels() {
  const container = document.getElementById('labels');
  container.innerHTML = '';
  labelElements = [];

  // 1. Primary 26 numbered locations
  campusData.locations.forEach((loc) => {
    const el = document.createElement('div');
    el.className = 'label';
    el.dataset.id = loc.id;

    const numSpan = document.createElement('span');
    numSpan.className = 'num';
    numSpan.textContent = loc.id;
    el.appendChild(numSpan);

    const textSpan = document.createElement('span');
    textSpan.className = 'txt';
    textSpan.textContent = loc.short || loc.name;
    el.appendChild(textSpan);

    const yOffset = (loc.floors || 2) * 4.2 + 5.8;
    const worldPos = new THREE.Vector3(loc.x, yOffset, loc.z);

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      selectAndFocusLocation(loc);
    });

    container.appendChild(el);
    labelElements.push({ el, worldPos, loc, isPrimary: true });
  });

  // 2. Secondary building labels for multi-building dorm/school clusters (like preview (1).webp)
  campusData.buildings.forEach((b) => {
    if (!b.loc) return;
    const loc = campusData.locations.find((l) => l.id === b.loc);
    if (!loc) return;
    const dist = Math.hypot(b.centroid[0] - loc.x, b.centroid[1] - loc.z);
    // Only add a secondary label if this building is a separate wing (> 18m from primary marker)
    if (dist < 18) return;

    const el = document.createElement('div');
    el.className = 'label sub-label';
    el.dataset.id = loc.id;

    const textSpan = document.createElement('span');
    textSpan.className = 'txt';
    textSpan.textContent = loc.short || loc.name;
    el.appendChild(textSpan);

    const yOffset = (loc.floors || 2) * 4.2 + 5.2;
    const worldPos = new THREE.Vector3(b.centroid[0], yOffset, b.centroid[1]);

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      selectAndFocusLocation(loc);
    });

    container.appendChild(el);
    labelElements.push({ el, worldPos, loc, isPrimary: false });
  });

  updateFloatingLabels();
}

function updateFloatingLabels() {
  if (!STATE.showLabels || labelElements.length === 0) return;

  const w = window.innerWidth;
  const h = window.innerHeight;
  const tempV = new THREE.Vector3();

  labelElements.forEach(({ el, worldPos, loc }) => {
    tempV.copy(worldPos);
    tempV.project(camera);

    if (tempV.z > 1.0 || tempV.x < -1.1 || tempV.x > 1.1 || tempV.y < -1.1 || tempV.y > 1.1) {
      el.classList.add('off');
      return;
    }

    el.classList.remove('off');
    const screenX = (tempV.x * 0.5 + 0.5) * w;
    const screenY = (-tempV.y * 0.5 + 0.5) * h;

    const dist = camera.position.distanceTo(worldPos);
    const scale = THREE.MathUtils.clamp(680 / dist, 0.78, 1.22);

    el.style.transform = `translate(-50%, -100%) translate3d(${screenX.toFixed(1)}px, ${screenY.toFixed(1)}px, 0) scale(${scale.toFixed(3)})`;

    if (loc.id === STATE.selectedId) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });
}

// ============================================================================
// 9. INTERACTIVE ORBIT, PAN, ZOOM & CAMERA ANIMATION
// ============================================================================
const BASE_ZOOM_RADIUS = 690;

function setToolMode(tool) {
  STATE.tool = tool;
  document.body.classList.remove('tool-select', 'tool-pan', 'tool-zoom');
  document.body.classList.add(`tool-${tool}`);
  document.querySelectorAll('.tool-switch button').forEach((b) => {
    b.classList.toggle('active', b.dataset.tool === tool);
  });
}

function panCameraByScreenDelta(dx, dy) {
  const panFactor = camState.radius * 0.00135;
  const right = new THREE.Vector3(Math.cos(camState.theta), 0, -Math.sin(camState.theta));
  const forward = new THREE.Vector3(Math.sin(camState.theta), 0, Math.cos(camState.theta));
  camState.targetLookAt.addScaledVector(right, -dx * panFactor);
  camState.targetLookAt.addScaledVector(forward, -dy * panFactor);
}

function handleTapOrClickAt(clientX, clientY, isShift = false) {
  mouse.x = (clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  if (STATE.tool === 'zoom') {
    // In Scale/Zoom tool mode, tapping zooms in (or Shift+Click zooms out) toward the tapped point
    const targetMesh = groundSatelliteMesh.visible ? groundSatelliteMesh : groundIllustratedMesh;
    const groundHits = raycaster.intersectObject(targetMesh, false);
    if (groundHits.length > 0) {
      const pt = groundHits[0].point;
      camState.targetLookAt.lerp(new THREE.Vector3(pt.x, 0, pt.z), 0.35);
    }
    const factor = isShift ? 1.25 : 0.78;
    camState.targetRadius = THREE.MathUtils.clamp(camState.targetRadius * factor, 130, 1400);
    return;
  }

  // In Select (Klik) or Hand tool mode, a clean tap/click without dragging selects a building
  const hits = raycaster.intersectObjects(interactiveMeshes, true);
  if (hits.length > 0) {
    let obj = hits[0].object;
    let locId = obj.userData.locationId;
    while (!locId && obj.parent) {
      obj = obj.parent;
      locId = obj.userData.locationId;
    }
    if (locId) {
      const loc = campusData.locations.find((l) => l.id === locId);
      if (loc) selectAndFocusLocation(loc);
    }
  }
}

function initControls() {
  const dom = renderer.domElement;
  document.body.classList.add(`tool-${STATE.tool}`);

  dom.addEventListener('mousedown', (e) => {
    camState.isDragging = true;
    document.body.classList.add('dragging');
    camState.isPanning = STATE.tool === 'pan' || e.button === 2 || e.shiftKey;
    camState.prevX = e.clientX;
    camState.prevY = e.clientY;
    camState.downX = e.clientX;
    camState.downY = e.clientY;
  });

  window.addEventListener('mousemove', (e) => {
    updateCursorCoordReadout(e);

    if (!camState.isDragging) return;
    const dx = e.clientX - camState.prevX;
    const dy = e.clientY - camState.prevY;
    camState.prevX = e.clientX;
    camState.prevY = e.clientY;

    if (STATE.tool === 'zoom' && !e.shiftKey && e.button === 0) {
      // Dragging vertically in Scale tool mode smoothly zooms in/out
      camState.targetRadius = THREE.MathUtils.clamp(camState.targetRadius + dy * 1.6, 130, 1400);
    } else if (camState.isPanning) {
      panCameraByScreenDelta(dx, dy);
    } else {
      camState.targetTheta -= dx * 0.0055;
      camState.targetPhi = THREE.MathUtils.clamp(camState.targetPhi - dy * 0.0055, 0.06, 1.38);
    }
  });

  window.addEventListener('mouseup', (e) => {
    if (!camState.isDragging) return;
    camState.isDragging = false;
    document.body.classList.remove('dragging');

    const moveDist = Math.hypot(e.clientX - camState.downX, e.clientY - camState.downY);
    if (moveDist < 6 && e.button === 0) {
      handleTapOrClickAt(e.clientX, e.clientY, e.shiftKey);
    }
  });

  dom.addEventListener('contextmenu', (e) => e.preventDefault());

  dom.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      camState.targetRadius = THREE.MathUtils.clamp(camState.targetRadius + e.deltaY * 0.45, 130, 1400);
    },
    { passive: false }
  );

  let touchStartDist = 0;
  dom.addEventListener(
    'touchstart',
    (e) => {
      if (e.touches.length === 1) {
        camState.isDragging = true;
        camState.isPanning = STATE.tool === 'pan';
        camState.prevX = e.touches[0].clientX;
        camState.prevY = e.touches[0].clientY;
        camState.downX = e.touches[0].clientX;
        camState.downY = e.touches[0].clientY;
      } else if (e.touches.length === 2) {
        camState.isDragging = false;
        touchStartDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
    },
    { passive: true }
  );

  dom.addEventListener(
    'touchmove',
    (e) => {
      if (e.touches.length === 1 && camState.isDragging) {
        const dx = e.touches[0].clientX - camState.prevX;
        const dy = e.touches[0].clientY - camState.prevY;
        camState.prevX = e.touches[0].clientX;
        camState.prevY = e.touches[0].clientY;

        if (STATE.tool === 'zoom') {
          camState.targetRadius = THREE.MathUtils.clamp(camState.targetRadius + dy * 1.8, 130, 1400);
        } else if (STATE.tool === 'pan' || camState.isPanning) {
          panCameraByScreenDelta(dx, dy);
        } else {
          camState.targetTheta -= dx * 0.0055;
          camState.targetPhi = THREE.MathUtils.clamp(camState.targetPhi - dy * 0.0055, 0.06, 1.38);
        }
      } else if (e.touches.length === 2) {
        const dist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const delta = touchStartDist - dist;
        camState.targetRadius = THREE.MathUtils.clamp(camState.targetRadius + delta * 1.2, 130, 1400);
        touchStartDist = dist;
      }
    },
    { passive: true }
  );

  dom.addEventListener('touchend', (e) => {
    if (camState.isDragging && e.changedTouches && e.changedTouches.length === 1) {
      const t = e.changedTouches[0];
      const moveDist = Math.hypot(t.clientX - camState.downX, t.clientY - camState.downY);
      if (moveDist < 8) {
        handleTapOrClickAt(t.clientX, t.clientY, false);
      }
    }
    camState.isDragging = false;
  });
}

function updateCameraPosition(immediate = false) {
  if (immediate) {
    camState.theta = camState.targetTheta;
    camState.phi = camState.targetPhi;
    camState.radius = camState.targetRadius;
    camState.target.copy(camState.targetLookAt);
  } else {
    camState.theta += (camState.targetTheta - camState.theta) * 0.1;
    camState.phi += (camState.targetPhi - camState.phi) * 0.1;
    camState.radius += (camState.targetRadius - camState.radius) * 0.1;
    camState.target.lerp(camState.targetLookAt, 0.1);
  }

  const x = camState.target.x + camState.radius * Math.sin(camState.phi) * Math.sin(camState.theta);
  const y = camState.target.y + camState.radius * Math.cos(camState.phi);
  const z = camState.target.z + camState.radius * Math.sin(camState.phi) * Math.cos(camState.theta);

  camera.position.set(x, y, z);
  camera.lookAt(camState.target);

  const needle = document.getElementById('compass-needle');
  if (needle) {
    const deg = THREE.MathUtils.radToDeg(camState.theta);
    needle.style.transform = `rotate(${deg}deg)`;
  }

  // Update live zoom percentage readout (100% at BASE_ZOOM_RADIUS = 690m)
  const zoomPctVal = document.getElementById('zoom-pct-val');
  if (zoomPctVal) {
    const pct = Math.round((BASE_ZOOM_RADIUS / Math.max(130, camState.radius)) * 100);
    zoomPctVal.textContent = `${pct}%`;
  }
}

function updateCursorCoordReadout(e) {
  const coordBox = document.getElementById('cursor-coord');
  if (!coordBox) return;

  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  const targetMesh = groundSatelliteMesh.visible ? groundSatelliteMesh : groundIllustratedMesh;
  const hits = raycaster.intersectObject(targetMesh, false);
  if (hits.length > 0) {
    const pt = hits[0].point;
    const M_PER_DEG_LAT = 110574.0;
    const M_PER_DEG_LNG = 111320.0 * Math.cos((ORIGIN.lat * Math.PI) / 180);
    const lat = ORIGIN.lat - pt.z / M_PER_DEG_LAT;
    const lng = ORIGIN.lng + pt.x / M_PER_DEG_LNG;
    coordBox.textContent = `${lat.toFixed(5)}° U, ${lng.toFixed(5)}° T`;
    coordBox.classList.remove('hidden');
  } else {
    coordBox.classList.add('hidden');
  }
}

// ============================================================================
// 10. LOCATION SELECTION, HUD CONTROLS, THEME & MODE SWITCHING
// ============================================================================
function selectAndFocusLocation(loc) {
  STATE.selectedId = loc.id;

  camState.targetLookAt.set(loc.x, 0, loc.z);
  camState.targetRadius = Math.min(camState.targetRadius, 340);

  const info = document.getElementById('info');
  document.getElementById('info-num').textContent = loc.id;
  document.getElementById('info-cat').textContent = loc.category || 'Fasilitas';
  document.getElementById('info-name').textContent = loc.name;
  document.getElementById('info-desc').textContent = loc.desc || '';
  document.getElementById('info-coord').textContent = `${loc.lat}, ${loc.lng}`;

  const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${loc.lat},${loc.lng}`;
  const routeUrl = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`;
  document.getElementById('info-gmaps').href = gmapsUrl;
  document.getElementById('info-route').href = routeUrl;

  info.classList.remove('hidden');
  updateFloatingLabels();
}

function initHUD() {
  document.getElementById('rot-left').addEventListener('click', () => {
    camState.targetTheta += Math.PI / 4;
  });
  document.getElementById('rot-right').addEventListener('click', () => {
    camState.targetTheta -= Math.PI / 4;
  });

  document.getElementById('zoom-in').addEventListener('click', () => {
    camState.targetRadius = Math.max(130, camState.targetRadius - 95);
  });
  document.getElementById('zoom-out').addEventListener('click', () => {
    camState.targetRadius = Math.min(1400, camState.targetRadius + 95);
  });
  const zoomPctBtn = document.getElementById('zoom-pct');
  if (zoomPctBtn) {
    zoomPctBtn.addEventListener('click', () => {
      camState.targetRadius = BASE_ZOOM_RADIUS;
    });
  }

  // Tool Switcher (Klik / Geser / Scale)
  document.querySelectorAll('.tool-switch button').forEach((btn) => {
    btn.addEventListener('click', () => {
      setToolMode(btn.dataset.tool);
    });
  });
  setToolMode(STATE.tool);

  document.getElementById('fit').addEventListener('click', () => {
    setViewPreset(STATE.view);
  });

  document.getElementById('compass').addEventListener('click', () => {
    setViewPreset('north');
    document.querySelectorAll('[data-setting="view"] button').forEach((b) => {
      b.classList.toggle('active', b.dataset.value === 'north');
    });
  });

  // Mode Switcher (Denah / Hybrid / Satelit)
  document.querySelectorAll('.mode-switch button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mode-switch button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      setMapMode(btn.dataset.mode);
    });
  });

  // Menu Drawer Toggle
  const menu = document.getElementById('menu');
  document.getElementById('menu-btn').addEventListener('click', () => {
    menu.classList.toggle('hidden');
  });

  // Close buttons
  document.querySelectorAll('[data-close]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.close);
      if (target) target.classList.add('hidden');
      if (btn.dataset.close === 'info') {
        STATE.selectedId = null;
        updateFloatingLabels();
      }
    });
  });

  // View Presets (Utara / Timur / Atas)
  document.querySelectorAll('[data-setting="view"] button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-setting="view"] button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      setViewPreset(btn.dataset.value);
    });
  });

  // Theme Segmented Control (Terang / Gelap)
  document.querySelectorAll('[data-setting="theme"] button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-setting="theme"] button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      setTheme(btn.dataset.value);
    });
  });

  // Trees Density Segmented Control (Tanpa / Sedang / Asli)
  document.querySelectorAll('[data-setting="trees"] button').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-setting="trees"] button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.trees = btn.dataset.value;
      applyTreeDensityMode();
    });
  });

  // Checkbox Toggles
  document.querySelector('[data-toggle="labels"]').addEventListener('change', (e) => {
    STATE.showLabels = e.target.checked;
    document.body.classList.toggle('no-labels', !STATE.showLabels);
    updateFloatingLabels();
  });

  document.querySelector('[data-toggle="numbers"]').addEventListener('change', (e) => {
    STATE.showNumbers = e.target.checked;
    document.body.classList.toggle('show-numbers', STATE.showNumbers);
  });

  document.querySelector('[data-toggle="shadows"]').addEventListener('change', (e) => {
    STATE.shadows = e.target.checked;
    renderer.shadowMap.enabled = STATE.shadows;
    dirLight.castShadow = STATE.shadows;
  });

  document.querySelector('[data-toggle="autorotate"]').addEventListener('change', (e) => {
    STATE.autoRotate = e.target.checked;
  });

  document.getElementById('copy-coord').addEventListener('click', () => {
    const text = document.getElementById('info-coord').textContent;
    navigator.clipboard.writeText(text);
    const btn = document.getElementById('copy-coord');
    btn.textContent = 'Tersalin!';
    setTimeout(() => {
      btn.textContent = 'Salin';
    }, 1800);
  });

  const gmapsModal = document.getElementById('gmaps-modal');
  document.getElementById('open-gmaps').addEventListener('click', () => {
    const iframe = gmapsModal.querySelector('iframe');
    if (!iframe.src && iframe.dataset.src) {
      iframe.src = iframe.dataset.src;
    }
    gmapsModal.classList.remove('hidden');
  });

  initSearch();
  populateDirectory();

  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === '/') {
      e.preventDefault();
      document.getElementById('search').focus();
    } else if (e.key === 'Escape') {
      document.getElementById('info').classList.add('hidden');
      document.getElementById('menu').classList.add('hidden');
      document.getElementById('gmaps-modal').classList.add('hidden');
      document.getElementById('results').classList.add('hidden');
      STATE.selectedId = null;
      updateFloatingLabels();
    } else if (e.key === 'n' || e.key === 'N') {
      setViewPreset('north');
    } else if (e.key === 'v' || e.key === 'V') {
      setToolMode('select');
    } else if (e.key === 'h' || e.key === 'H') {
      setToolMode('pan');
    } else if (e.key === 'z' || e.key === 'Z') {
      setToolMode('zoom');
    }
  });
}

function setViewPreset(viewName) {
  const preset = VIEW_PRESETS[viewName] || VIEW_PRESETS.north;
  STATE.view = viewName;
  camState.targetTheta = preset.theta;
  camState.targetPhi = preset.phi;
  camState.targetRadius = preset.radius;
  camState.targetLookAt.copy(preset.lookAt);
}

function setMapMode(mode) {
  STATE.mode = mode;

  if (mode === 'illustrated') {
    groundIllustratedMesh.visible = true;
    groundSatelliteMesh.visible = false;
    buildingsGroup.visible = true;
    landmarksGroup.visible = true;
    roadsGroup.visible = true;
    riversGroup.visible = true;
    fieldsGroup.visible = true;
    MATS.roadYellow.transparent = false;
    MATS.roadYellow.opacity = 1.0;
    applyTreeDensityMode();
  } else if (mode === 'hybrid') {
    groundIllustratedMesh.visible = false;
    groundSatelliteMesh.visible = true;
    buildingsGroup.visible = true;
    landmarksGroup.visible = true;
    roadsGroup.visible = true;
    riversGroup.visible = false;
    fieldsGroup.visible = true;
    MATS.roadYellow.transparent = true;
    MATS.roadYellow.opacity = 0.72;
    applyTreeDensityMode();
  } else if (mode === 'satellite') {
    groundIllustratedMesh.visible = false;
    groundSatelliteMesh.visible = true;
    buildingsGroup.visible = false;
    landmarksGroup.visible = false;
    roadsGroup.visible = false;
    riversGroup.visible = false;
    fieldsGroup.visible = false;
    applyTreeDensityMode();
  }
}

function setTheme(theme) {
  STATE.theme = theme;
  document.body.classList.toggle('dark', theme === 'dark');

  const p = PALETTES[theme];

  scene.background.setHex(p.bg);
  MATS.ground.color.setHex(p.ground);
  MATS.forestFloor.color.setHex(p.forestFloor);
  MATS.slabWall.color.setHex(p.slabWall);
  MATS.slabSkirt.color.setHex(p.slabSkirt);
  MATS.boundaryRed.color.setHex(p.boundaryRed);

  MATS.roadAsphalt.color.setHex(p.roadAsphalt);
  MATS.roadShoulder.color.setHex(p.roadShoulder);
  MATS.roadYellow.color.setHex(p.roadYellow);
  MATS.roadYellowBorder.color.setHex(p.roadYellowBorder);

  MATS.riverWater.color.setHex(p.riverWater);
  MATS.riverBank.color.setHex(p.riverBank);

  MATS.buildingWall.color.setHex(p.buildingWall);
  MATS.buildingParapet.color.setHex(p.buildingParapet);
  MATS.buildingFlatRoof.color.setHex(p.buildingFlatRoof);
  MATS.buildingPitchedRoof.color.setHex(p.buildingPitchedRoof);

  MATS.treeTrunk.color.setHex(p.treeTrunk);
  MATS.palmTrunk.color.setHex(p.palmTrunk);
  MATS.palmFrond.color.setHex(p.palmFrond);
  MATS.conifer.color.setHex(p.conifer);

  updateTreeCanopyColors();

  // Swap court textures between light and dark versions
  fieldsGroup.children.forEach((child) => {
    if (child.isMesh && child.material && child.material.userData.texLight) {
      child.material.map = theme === 'dark' ? child.material.userData.texDark : child.material.userData.texLight;
      child.material.needsUpdate = true;
    }
  });

  dirLight.color.setHex(p.dirLightColor);
  dirLight.intensity = p.dirLightIntensity;
  hemiLight.color.setHex(p.hemiSky);
  hemiLight.groundColor.setHex(p.hemiGround);
  hemiLight.intensity = p.hemiIntensity;
  ambientLight.intensity = p.ambientIntensity;
}

function initSearch() {
  const input = document.getElementById('search');
  const results = document.getElementById('results');

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (!q) {
      results.classList.add('hidden');
      return;
    }

    const matches = campusData.locations.filter((loc) => {
      return (
        loc.id.toString() === q ||
        loc.name.toLowerCase().includes(q) ||
        (loc.short && loc.short.toLowerCase().includes(q)) ||
        (loc.category && loc.category.toLowerCase().includes(q))
      );
    });

    results.innerHTML = '';
    if (matches.length === 0) {
      results.innerHTML = '<li style="color:var(--ink-3)">Tidak ada lokasi ditemukan</li>';
    } else {
      matches.forEach((loc) => {
        const li = document.createElement('li');
        li.innerHTML = `
          <span class="n">${loc.id}</span>
          <span>${loc.name}</span>
          <small>${loc.category || ''}</small>
        `;
        li.addEventListener('click', () => {
          selectAndFocusLocation(loc);
          results.classList.add('hidden');
          input.value = '';
        });
        results.appendChild(li);
      });
    }
    results.classList.remove('hidden');
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      results.classList.add('hidden');
      input.blur();
    }
  });
}

function populateDirectory() {
  const list = document.getElementById('directory');
  list.innerHTML = '';

  campusData.locations.forEach((loc) => {
    const li = document.createElement('li');
    li.innerHTML = `
      <span class="n">${loc.id}</span>
      <span>${loc.name}</span>
      <small>${loc.category || ''}</small>
    `;
    li.addEventListener('click', () => {
      selectAndFocusLocation(loc);
      document.getElementById('menu').classList.add('hidden');
    });
    list.appendChild(li);
  });
}

// ============================================================================
// 11. ANIMATION LOOP & BOOTSTRAP
// ============================================================================
function animate() {
  timer.update();
  const delta = timer.getDelta();

  if (STATE.autoRotate && !camState.isDragging) {
    camState.targetTheta += delta * 0.12;
  }

  if (globeMesh) {
    globeMesh.rotation.y += delta * 0.55;
  }

  updateCameraPosition(false);
  updateFloatingLabels();
  renderer.render(scene, camera);
}

async function start() {
  const loaderEl = document.getElementById('loader');

  try {
    // Support both fetched JSON (Vite dev/build) and inlined offline data
    if (window.__CAMPUS_DATA__) {
      campusData = window.__CAMPUS_DATA__;
    } else {
      const res = await fetch(CAMPUS_DATA_URL);
      campusData = await res.json();
    }

    const textureLoader = new THREE.TextureLoader();
    const satUrl = window.__SATELLITE_DATA_URI__ || campusData.satellite.url;
    satelliteTexture = await new Promise((resolve) => {
      textureLoader.load(
        satUrl,
        (tex) => {
          tex.colorSpace = THREE.SRGBColorSpace;
          tex.wrapS = THREE.ClampToEdgeWrapping;
          tex.wrapT = THREE.ClampToEdgeWrapping;
          resolve(tex);
        },
        undefined,
        () => resolve(null)
      );
    });

    initScene();

    buildDioramaBase();
    buildRivers();
    buildYellowRoads();
    buildFields();
    buildBuildings();
    buildVegetation();

    initFloatingLabels();
    initHUD();

    // Support URL query parameters for deep-linking & visual verification
    const params = new URLSearchParams(window.location.search);
    if (params.get('theme') === 'dark' || params.get('theme') === 'light') {
      setTheme(params.get('theme'));
      document.querySelectorAll('[data-setting="theme"] button').forEach((b) => {
        b.classList.toggle('active', b.dataset.value === params.get('theme'));
      });
    }
    if (params.get('mode')) {
      setMapMode(params.get('mode'));
      document.querySelectorAll('.mode-switch button').forEach((b) => {
        b.classList.toggle('active', b.dataset.mode === params.get('mode'));
      });
    }
    if (params.get('trees')) {
      STATE.trees = params.get('trees');
      applyTreeDensityMode();
      document.querySelectorAll('[data-setting="trees"] button').forEach((b) => {
        b.classList.toggle('active', b.dataset.value === params.get('trees'));
      });
    }
    if (params.get('labels') === '0') {
      STATE.showLabels = false;
      document.body.classList.add('no-labels');
      const chk = document.querySelector('[data-toggle="labels"]');
      if (chk) chk.checked = false;
    }
    if (params.get('view')) {
      setViewPreset(params.get('view'));
      updateCameraPosition(true);
      document.querySelectorAll('[data-setting="view"] button').forEach((b) => {
        b.classList.toggle('active', b.dataset.value === params.get('view'));
      });
    }

    // Expose debug/inspection hook for automated verification
    window.__DENAH_APP__ = {
      setMapMode,
      setTheme,
      setViewPreset,
      setTrees: (val) => {
        STATE.trees = val;
        applyTreeDensityMode();
      },
      STATE,
    };

    renderer.setAnimationLoop(animate);

    loaderEl.classList.add('done');
    setTimeout(() => {
      loaderEl.remove();
    }, 600);
  } catch (err) {
    console.error('Failed to load 3D campus:', err);
    loaderEl.innerHTML = `<p style="color:#ef4444">Gagal memuat data 3D: ${err.message}</p>`;
  }
}

window.addEventListener('DOMContentLoaded', start);
