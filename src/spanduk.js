import './spanduk.css';

const MARKERS_URL = '/data/mading_markers.json';

const PIN_OFFSETS = {
  1:  { dx: 0.0,  dy: -1.8 },
  2:  { dx: 1.4,  dy: 0.8 },
  4:  { dx: -1.2, dy: 0.0 },
  26: { dx: 1.5,  dy: 0.5 },
  6:  { dx: 0.8,  dy: 0.0 },
  24: { dx: -1.5, dy: 0.6 },
  9:  { dx: 1.5,  dy: 0.0 },
  25: { dx: -1.8, dy: 0.0 },
  20: { dx: -1.5, dy: -0.8 },
  21: { dx: 1.2,  dy: 1.2 },
};

let markersData = [];
let selectedId = null;
let mapStyleMode = '2d';

// Scales the 1600x1136 board proportionally on narrower screens so it NEVER wraps or squeezes
function fitBoardToViewport() {
  const board = document.getElementById('spanduk-board');
  const stage = document.querySelector('.spanduk-stage');
  if (!board || !stage) return;

  const availW = window.innerWidth - 28;
  const scale = Math.min(1, Math.max(0.35, availW / 1600));
  board.style.transform = `scale(${scale.toFixed(4)})`;
  stage.style.height = `${Math.ceil(1136 * scale + 44)}px`;
}

async function initSpanduk() {
  try {
    if (window.__MADING_MARKERS__) {
      markersData = window.__MADING_MARKERS__;
    } else {
      const res = await fetch(MARKERS_URL);
      markersData = await res.json();
    }

    renderMapMarkers();
    renderKeteranganList();
    bindToolbarAndPhotos();
    fitBoardToViewport();

    window.addEventListener('resize', fitBoardToViewport);
    window.addEventListener('beforeprint', () => {
      const board = document.getElementById('spanduk-board');
      const stage = document.querySelector('.spanduk-stage');
      if (board) board.style.transform = 'none';
      if (stage) stage.style.height = '1136px';
    });
    window.addEventListener('afterprint', fitBoardToViewport);
  } catch (err) {
    console.error('Failed to initialize Spanduk Mading:', err);
  }
}

function renderMapMarkers() {
  const ilusLayer = document.getElementById('markers-ilustrasi');
  const satLayer = document.getElementById('markers-satelit');
  if (satLayer) satLayer.innerHTML = '';
  if (!ilusLayer) return;

  ilusLayer.innerHTML = '';

  markersData.forEach((loc) => {
    const off = PIN_OFFSETS[loc.id] || { dx: 0, dy: 0 };
    const left = loc.left + off.dx;
    const top = loc.top + off.dy;

    const pin = document.createElement('button');
    pin.className = 'map-pin-badge';
    pin.dataset.id = loc.id;
    pin.style.left = left.toFixed(2) + '%';
    pin.style.top = top.toFixed(2) + '%';
    pin.style.setProperty('--pin-bg', loc.color);
    pin.textContent = loc.id;
    pin.title = `${loc.id}. ${loc.name} (${loc.category})`;

    pin.addEventListener('click', (e) => {
      e.stopPropagation();
      selectLocation(loc.id);
    });

    ilusLayer.appendChild(pin);
  });
}

function renderKeteranganList() {
  const container = document.getElementById('keterangan-grid');
  if (!container) return;
  container.innerHTML = '';

  const isV2 = container.classList.contains('v2-keterangan-grid');
  const reordered = [];

  if (isV2) {
    const cols = 3;
    const rows = Math.ceil(markersData.length / cols);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const idx = c * rows + r;
        if (markersData[idx]) reordered.push(markersData[idx]);
      }
    }
  } else {
    const half = Math.ceil(markersData.length / 2);
    for (let row = 0; row < half; row++) {
      if (markersData[row]) reordered.push(markersData[row]);
      if (markersData[row + half]) reordered.push(markersData[row + half]);
    }
  }

  const SHORT_LABELS = {
    13: 'R. TU, Perpustakaan & Aula',
    14: 'Gedung Adm. & R. Turkey',
    16: 'Gedung Turkey / Sekolah',
    19: 'Dapur & Ruang Makan Putri',
    20: 'Kantin Putri & Mess Ustazah',
  };

  reordered.forEach((loc) => {
    const item = document.createElement('div');
    item.className = 'ket-item';
    item.dataset.id = loc.id;
    item.title = `${loc.id}. ${loc.name} — Klik untuk sorot di peta`;
    const labelText = SHORT_LABELS[loc.id] || loc.name;

    item.innerHTML = `
      <span class="ket-badge" style="--pin-bg: ${loc.color}">${loc.id}</span>
      <span class="ket-name">${labelText}</span>
    `;

    item.addEventListener('click', () => {
      selectLocation(loc.id);
    });

    container.appendChild(item);
  });
}

function selectLocation(id) {
  selectedId = id;
  const loc = markersData.find((m) => m.id === Number(id));
  if (!loc) return;

  document.querySelectorAll('.map-pin-badge').forEach((el) => {
    el.classList.toggle('active', Number(el.dataset.id) === loc.id);
  });

  document.querySelectorAll('.ket-item').forEach((el) => {
    el.classList.toggle('active', Number(el.dataset.id) === loc.id);
  });

  const inspector = document.getElementById('mading-inspector');
  if (inspector) {
    const badge = document.getElementById('insp-badge');
    badge.textContent = loc.id;
    badge.style.background = loc.color;
    document.getElementById('insp-title').textContent = `${loc.name} (${loc.category})`;
    document.getElementById('insp-desc').textContent = `${loc.desc} · Koordinat: ${loc.lat.toFixed(5)}° U, ${loc.lng.toFixed(5)}° T`;
    document.getElementById('insp-gmaps').href = `https://www.google.com/maps/search/?api=1&query=${loc.lat},${loc.lng}`;
    inspector.classList.remove('hidden');
  }
}

function bindToolbarAndPhotos() {
  const imgIlus = document.getElementById('img-ilustrasi');
  const imgSat = document.getElementById('img-satelit');
  const markersIlus = document.getElementById('markers-ilustrasi');
  const markersSat = document.getElementById('markers-satelit');
  const v2MapStage = document.getElementById('v2-map-stage');
  const v2SatInset = document.getElementById('v2-satelite-inset');
  const v2MainRibbon = document.getElementById('v2-main-ribbon-tab');
  const v2InsetTitle = document.getElementById('v2-inset-tab-title');
  let v2Swapped = false;

  function applyMapImages() {
    const ilusSrc = mapStyleMode === '3d'
      ? (window.__IMG_3D_ILUS__ || '/textures/render_3d_ilustrasi.png')
      : (window.__IMG_2D_ILUS__ || '/textures/mading_ilustrasi.jpg');
    const satSrc = mapStyleMode === '3d'
      ? (window.__IMG_3D_SAT__ || '/textures/render_3d_satelit.png')
      : (window.__IMG_2D_SAT__ || '/textures/mading_satelit.jpg');

    if (v2Swapped) {
      if (imgIlus) imgIlus.src = satSrc;
      if (imgSat) imgSat.src = ilusSrc;
    } else {
      if (imgIlus) imgIlus.src = ilusSrc;
      if (imgSat) imgSat.src = satSrc;
    }

    const showPins = mapStyleMode !== '3d';
    // Numbered markers only shown on the illustrated map, NEVER on the satellite map
    if (markersIlus) {
      markersIlus.style.display = (showPins && !v2Swapped) ? 'block' : 'none';
    }
    if (markersSat) {
      markersSat.style.display = 'none';
    }

    if (v2MapStage) {
      v2MapStage.classList.toggle('style-3d', mapStyleMode === '3d' && !v2Swapped);
      v2MapStage.classList.toggle('main-is-satelit', v2Swapped);
    }
  }

  document.querySelectorAll('[data-map-style]').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-map-style]').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      mapStyleMode = btn.dataset.mapStyle;
      applyMapImages();
    });
  });

  if (v2SatInset) {
    v2SatInset.addEventListener('click', (e) => {
      if (e.target.closest('.map-pin-badge')) return;
      v2Swapped = !v2Swapped;
      if (v2MainRibbon) {
        v2MainRibbon.textContent = v2Swapped ? 'Denah Satelit' : 'Denah Ilustrasi';
      }
      if (v2InsetTitle) {
        v2InsetTitle.textContent = v2Swapped ? 'ILUSTRASI' : 'SATELITE';
      }
      applyMapImages();
    });
  }

  const printBtn = document.getElementById('btn-print');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  const closeBtn = document.getElementById('insp-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('mading-inspector').classList.add('hidden');
      selectedId = null;
      document.querySelectorAll('.map-pin-badge, .ket-item').forEach((el) => el.classList.remove('active'));
    });
  }

  document.querySelectorAll('.photo-card[data-loc-id]').forEach((card) => {
    card.addEventListener('click', () => {
      selectLocation(Number(card.dataset.locId));
    });
  });
}

window.addEventListener('DOMContentLoaded', initSpanduk);
