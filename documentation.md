# 📘 Panduan Pengelolaan & Pemeliharaan Denah Digital 3D
### Pesantren Modern Tgk. Chiek Oemar Diyan

Dokumen ini disusun sebagai panduan teknis bagi pengelola, pengembang, maupun pengurus pesantren di masa mendatang untuk melakukan pemeliharaan, pengeditan teks/judul (*title*), penyesuaian label 3D, serta penambahan pemetaan bangunan baru pada sistem Denah 3D Interaktif.

---

## 📑 Daftar Isi

1. [Struktur Berkas & Arsitektur Data](#1-struktur-berkas--arsitektur-data)
2. [Sistem Koordinat Denah](#2-sistem-koordinat-denah)
3. [Mekanisme Mengedit Judul & Keterangan Lokasi](#3-mekanisme-mengedit-judul--keterangan-lokasi)
   - [3.1 Mengubah Nama Lokasi Utama (1–26)](#31-mengubah-nama-lokasi-utama-126)
   - [3.2 Mengatur Teks & Perilaku Floating Label 3D](#32-mengatur-teks--perilaku-floating-label-3d)
   - [3.3 Mencegah Judul Ganda (Double Title) pada Satu Kompleks Gedung](#33-mencegah-judul-ganda-double-title-pada-satu-kompleks-gedung)
4. [Mekanisme Menambah Pemetaan Bangunan Baru](#4-mekanisme-menambah-pemetaan-bangunan-baru)
   - [4.1 Menambah Bangunan Rumah/Gedung Sederhana (Tanpa Title)](#41-menambah-bangunan-rumahgedung-sederhana-tanpa-title)
   - [4.2 Menambah Bangunan Fasilitas Resmi Baru (Dengan Title & Nomor)](#42-menambah-bangunan-fasilitas-resmi-baru-dengan-title--nomor)
5. [Tipe Atap & Karakteristik Arsitektur 3D](#5-tipe-atap--karakteristik-arsitektur-3d)
6. [Alur Kompilasi & Pembaruan Sistem (Build & Offline Export)](#6-alur-kompilasi--pembaruan-sistem-build--offline-export)

---

## 1. Struktur Berkas & Arsitektur Data

Sistem denah 3D memisahkan antara data geospasial (JSON) dan kode logika render visual (JavaScript/Three.js):

| Berkas | Fungsi & Peran |
| :--- | :--- |
| `public/data/campus.json` | **Pusat data spasial**: memuat daftar 26 lokasi POI (`locations`), geometri poligon gedung (`buildings`), jaringan jalan (`roadsMain`, `roadsCore`, `roadsInternal`), sungai, lapangan, dan vegetasi. |
| `src/main.js` | **Logika aplikasi 3D**: ekstrusi bangunan Three.js, pencahayaan, orbit kamera, sistem floating labels 3D, panel HUD, dan pencarian. |
| `src/style.css` | Styling antarmuka (UI), badge nomor, kartu info, HUD, serta floating label 3D. |
| `tools/generate_standalone.py` | Skrip generator untuk menghasilkan berkas offline tunggal (*zero-dependency* HTML). |

---

## 2. Sistem Koordinat Denah

Denah 3D menggunakan sistem koordinat kartesius berbasis meter dengan titik acuan nol (*origin*) di tengah kampus:
* **Titik Pusat / Origin GPS:** `Lat: 5.399226°, Lng: 95.435794°` (dekat Tugu Globe).
* **Sumbu X:** Mengarah ke Timur (+) dan Barat (-).
* **Sumbu Z:** Mengarah ke Selatan (+) dan Utara (-).
* **Sumbu Y:** Ketinggian vertikal (lantai & atap).

> **Rumus Konversi Cepat (Estimasi di Wilayah Aceh Besar):**
> * $1^\circ \text{ Lintang (Lat)}$ $\approx 110.574 \text{ meter}$ ($\Delta z \approx -(\text{lat} - \text{origin.lat}) \times 110574$)
> * $1^\circ \text{ Bujur (Lng)}$ $\approx 110.852 \text{ meter}$ ($\Delta x \approx (\text{lng} - \text{origin.lng}) \times 110852$)

---

## 3. Mekanisme Mengedit Judul & Keterangan Lokasi

### 3.1 Mengubah Nama Lokasi Utama (1–26)
Untuk mengubah nama gedung, kategori, maupun deskripsi yang muncul pada **pencarian** dan **kartu detail info**, edit berkas:
📂 [`public/data/campus.json`](file:///d:/PPKPM/denah/public/data/campus.json) pada array `"locations"`:

```json
{
  "id": 19,
  "name": "Dapur & Ruang Makan Putri",
  "short": "Dapur Putri",
  "category": "Konsumsi",
  "kind": "building",
  "floors": 1,
  "roof": "gable",
  "desc": "Dua ruang dapur dan ruang makan putri.",
  "lat": 5.3978564,
  "lng": 95.4358764,
  "x": 9.13,
  "z": 151.45
}
```
* `name`: Nama lengkap yang muncul di panel kartu informasi saat gedung diklik.
* `short`: Nama ringkas default untuk label melayang di atas gedung.
* `desc`: Deskripsi fungsi gedung.
* `category`: Kategori fasilitas (`"Pendidikan"`, `"Ibadah"`, `"Asrama"`, `"Konsumsi"`, dll).

---

### 3.2 Mengatur Teks & Perilaku Floating Label 3D
Sistem label 3D diatur di dalam fungsi `initFloatingLabels()` pada berkas:
📂 [`src/main.js`](file:///d:/PPKPM/denah/src/main.js) (sekitar baris 1250–1330).

#### A. Mengubah Teks Label Utama (Primary Label)
Label utama membawa nomor pin bulat merah (1–26). Jika ingin memberi teks khusus (misal: Lokasi 19 diubah menjadi `"Dapur"`):

```javascript
// Di dalam loop campusData.locations.forEach((loc) => { ... })
if (loc.id === 19) {
  textSpan.textContent = 'Dapur';
} else {
  textSpan.textContent = loc.short || loc.name;
}
```

#### B. Menggeser Posisi Penanda Nomor / Label Utama
Jika posisi label default (`loc.x`, `loc.z`) kurang pas di tengah atap gedung:
```javascript
let posX = loc.x;
let posZ = loc.z;

if (loc.id === 19) {
  posX = 0.76;     // Geser ke tengah gedung dapur
  posZ = 161.11;
} else if (loc.id === 3) {
  posX = -28.99;   // Geser ke tengah gedung MTsN
  posZ = -190.37;
}

const worldPos = new THREE.Vector3(posX, yOffset, posZ);
```

---

### 3.3 Mencegah Judul Ganda (Double Title) pada Satu Kompleks Gedung
Secara default, jika suatu fasilitas memiliki beberapa sayap gedung yang berjarak $> 18\text{ meter}$, sistem otomatis membuat *sub-label*. 

Untuk membatasi atau meniadakan judul dobel pada gedung tertentu (seperti pada **MTsN**, **Kantin Putri**, dan **Dapur**), aturan diatur pada loop kedua `campusData.buildings.forEach`:

```javascript
// 1. Lewati sub-label agar hanya memiliki 1 title utama:
if (b.loc === 3 || b.loc === 20) return; // MTsN & Kantin Putri cukup 1 title

// 2. Beri sub-label khusus hanya untuk sayap tertentu:
if (b.loc === 19) {
  // Hanya tampilkan label kedua untuk gedung Ruang Makan Putri (sayap utara, z < 145)
  if (b.centroid[1] < 145) {
    const textSpan = document.createElement('span');
    textSpan.className = 'txt';
    textSpan.textContent = 'Ruang Makan Putri';
    // ... pasang label ...
  }
  return; // Sayap gudang/dapur belakang dilewati
}
```

---

## 4. Mekanisme Menambah Pemetaan Bangunan Baru

### 4.1 Menambah Bangunan Rumah/Gedung Sederhana (Tanpa Title)
Jika terdapat bangunan rumah warga, pos pendukung, atau gudang kecil yang **hanya ingin ditampilkan bentuk 3D-nya saja tanpa label/title/nomor**:

Buka [`public/data/campus.json`](file:///d:/PPKPM/denah/public/data/campus.json) dan tambahkan objek baru ke dalam array `"buildings"`:

```json
{
  "outer": [
    [10.0, 216.0],
    [28.0, 221.0],
    [25.0, 232.0],
    [7.0, 227.0]
  ],
  "holes": [],
  "loc": null,
  "floors": 1,
  "roof": "hip",
  "centroid": [17.5, 224.0]
}
```

#### Keterangan Properti:
* `"outer"`: Daftar koordinat titik sudut poligon pondasi `[x, z]` (satuan meter relatif terhadap origin).
* `"holes"`: Ruang kosong/inner courtyard (kosongkan `[]` jika tidak ada void di tengah gedung).
* `"loc": null`: **Penting!** Nilai `null` memastikan bangunan ini tidak memiliki keterkaitan dengan nomor POI dan tidak memunculkan label melayang.
* `"floors"`: Jumlah lantai (contoh: `1` untuk rumah sederhana, `2` atau `3` untuk gedung asrama).
* `"roof"`: Model atap (`"hip"` untuk limasan, `"flat"` untuk dak datar, `"gable"` untuk pelana).
* `"centroid"`: Titik tengah poligon `[rata-rata x, rata-rata z]` untuk penempatan atap dan orientasi Three.js.

---

### 4.2 Menambah Bangunan Fasilitas Resmi Baru (Dengan Title & Nomor)
Jika pesantren membangun fasilitas resmi baru (misal gedung nomor `27`):

1. **Tambahkan data POI ke `"locations"` di `campus.json`:**
   ```json
   {
     "id": 27,
     "name": "Laboratorium Komputer & Bahasa",
     "short": "Lab Komputer",
     "category": "Pendidikan",
     "kind": "building",
     "floors": 2,
     "roof": "flat",
     "desc": "Gedung laboratorium komputer dan multimedia.",
     "lat": 5.399500,
     "lng": 95.436200,
     "x": 45.0,
     "z": 10.0
   }
   ```
2. **Tambahkan poligon bangunan ke `"buildings"` di `campus.json`:**
   Isi properti `"loc": 27`. Dengan mengisi nomor `loc`, sistem 3D secara otomatis:
   * Menghubungkan klik mouse/sentuhan pada gedung dengan kartu informasi nomor 27.
   * Menampilkan floating label dengan nomor `27` dan nama `"Lab Komputer"`.
   * Menambahkan gedung ke sistem pencarian instan HUD.

---

## 5. Tipe Atap & Karakteristik Arsitektur 3D

Mesin render Three.js di [`src/main.js`](file:///d:/PPKPM/denah/src/main.js) mendukung beberapa gaya arsitektur yang otomatis disesuaikan dengan nilai `"roof"`:

| Nilai `"roof"` | Bentuk Visual 3D | Penggunaan di Kampus |
| :--- | :--- | :--- |
| `"hip"` / `"gable"` | Atap limasan/pelana miring prosedural (*Oriented Hipped Roof*) | Rumah hunian, ruang makan putra, dapur, aula kecil. |
| `"flat"` | Dak atap beton dengan lis parapet timbul (*Raised Parapet Rim*) | Gedung sekolah MTsN, GTS, asrama putra/putri, administrasi. |
| `"mosque"` | Kubah hijau besar + ornamen bulan bintang + menara masjid | Masjid Baburrayyan (Lokasi 4). |
| `"dome"` | Kubah separuh bola hijau emerald | Musalla Putri (Lokasi 17). |

---

## 6. Alur Kompilasi & Pembaruan Sistem (Build & Offline Export)

Setelah melakukan perubahan pada `campus.json` atau `src/main.js`, lakukan langkah berikut:

### 1. Menjalankan Server Percobaan (Local Development)
```bash
npm run dev
```
Buka URL lokal (biasanya `http://localhost:5173/`) pada browser untuk memeriksa hasil 3D secara langsung dengan fitur *Hot Module Replacement (HMR)*.

### 2. Melakukan Kompilasi untuk Web Production
```bash
npm run build
```
Perintah ini akan memproses, meminimalkan aset, dan menyalin data terbaru ke dalam folder `dist/`.

### 3. Memperbarui Berkas Mandiri Offline (Zero-Dependency HTML)
```bash
npm run standalone
```
* Skrip ini akan mengemas seluruh kode CSS, JS, tekstur satelit (Base64), dan data JSON terbaru langsung ke dalam berkas tunggal:
  * `denah_3d_offline.html` (Aplikasi Denah 3D tanpa butuh server/internet)
  * `spanduk_mading_offline.html` (Spanduk Mading interaktif offline)
* Berkas offline ini dapat langsung dipindahkan ke flashdisk dan dibuka di komputer mana pun hanya dengan *double-click* pada web browser biasa (Chrome, Edge, Firefox).

---

*Dokumentasi ini disusun oleh Tim PPKPM 26 UIN Ar-Raniry Banda Aceh untuk Pesantren Modern Tgk. Chiek Oemar Diyan.*

