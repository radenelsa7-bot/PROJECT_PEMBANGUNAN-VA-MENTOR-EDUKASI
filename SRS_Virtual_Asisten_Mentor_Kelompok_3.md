## SPESIFIKASI KEBUTUHAN PERANGKAT LUNAK

(Software Requirements Specification / SRS)

## VIRTUAL ASISTEN MENTOR EDUKASI BERBASIS PYTHON & AI MODEL API

Disusun oleh: KELOMPOK 3

| Nama | NPM |
| --- | --- |
| R. Elsa Balqis Khoerunnisa. S | 20241320062 |
| Amara Sylvi Yuliana | 20241320072 |
| Moch Adhi R | 20241320089 |
| M Rifqy Wildan | 20241320055 |
| Nabilah Asana Alecia | 20241320076 |


## 1. PENDAHULUAN

## 1.1 Tujuan

Dokumen SRS ini mendefinisikan kebutuhan fungsional dan nonfungsional sistem Virtual Asisten Mentor Edukasi, yaitu aplikasi berbasis Python yang terintegrasi dengan AI Model API (Large Language Model) untuk berperan sebagai mentor pendidikan yang adaptif, terstruktur, dan interaktif. Dokumen ini disusun berdasarkan Kerangka Acuan Kerja (KAK) Kelompok 8 dan ditujukan bagi Project Manager / Systems Analyst, Python Backend Developer, AI / Prompt Engineer, penguji, serta pihak pengelola sistem.

Masalah dan tujuan bisnis yang menjadi dasar seluruh kebutuhan dalam dokumen ini adalah sebagai berikut.

Masalah: pembelajar mengalami information overload sehingga kesulitan menyaring informasi tanpa arah belajar yang jelas, sementara kebutuhan pembelajaran yang dipersonalisasi sangat tinggi.

| ID | Tujuan Bisnis (Business Goal) | Sumber KAK |
| --- | --- | --- |
|   | BG-01 Menyediakan jalur belajar (learning path) terstruktur dalam modul-modul kecil berupa poin bacaan wajib. | I.2.b |
|   | BG-02 Membimbing pengguna secara interaktif sebelum diizinkan melanjutkan ke materi berikutnya. | I.2.b |
|   | BG-03 Memanfaatkan AI API untuk penjelasan kontekstual, analogi sederhana, dan evaluasi pemahaman. | I.2.b |
|   | BG-04 Menghasilkan sistem backend yang stabil dan konsisten sesuai kurikulum, tanpa halusinasi di luar materi. | I.3, III.1 |

## 1.2 Ruang Lingkup

Produk yang dikembangkan bernama Virtual Asisten Mentor Edukasi. Ruang lingkup pengembangan meliputi:

- Perancangan skema database kurikulum dan poin bacaan wajib.

- Pengembangan logika inti (Core Engine) berbasis Python dengan sistem status belajar (state machine).

- Integrasi AI Model API dengan konfigurasi System Prompt khusus mentor.

- Pengujian dan debugging sistem untuk mencegah halusinasi AI di luar materi kurikulum.

- Penyusunan dokumentasi API dan panduan penggunaan.

Di luar ruang lingkup: pengembangan aplikasi mobile native, pelatihan (training) model AI sendiri, sistem pembayaran, serta penyediaan perangkat keras khusus.


Keluaran (output): purwarupa (prototype) aplikasi dan dokumentasi API yang lengkap. Hasil (outcome): tersedianya sarana belajar mandiri yang interaktif, terstruktur, dan akurat.

## 1.3 Definisi dan Singkatan

| Istilah | Definisi |
| --- | --- |
| SRS | Software Requirements Specification, dokumen spesifikasi kebutuhan perangkat lunak. |
| KAK | Kerangka Acuan Kerja, dokumen acuan awal proyek. |
| FR | Functional Requirement, kebutuhan fungsional. |
| NFR | Non-Functional Requirement, kebutuhan nonfungsional (kinerja, keamanan, dan atribut kualitas lain). |
| Pembelajar | Pengguna akhir yang belajar melalui sistem. |
| Administrator | Pengelola yang mengatur kurikulum, poin bacaan, dan konfigurasi AI. |
| Kurikulum | Kumpulan materi pembelajaran yang disusun dalam beberapa modul. |
| Modul | Unit materi kecil dalam kurikulum yang berisi poin bacaan wajib dan soal evaluasi. |
|   | Poin Bacaan Wajib Ringkasan materi inti yang harus dibaca pembelajar sebelum berdiskusi atau dievaluasi. |
| Learning Path | Urutan modul yang harus ditempuh pembelajar. |
| Mentor AI | Fungsi asisten berbasis LLM yang menjelaskan materi dan mengevaluasi pemahaman. |
| LLM | Large Language Model, model bahasa besar yang diakses melalui API. |
| System Prompt | Instruksi dasar yang mengatur peran dan batasan perilaku Mentor AI. |
| State Machine | Mekanisme pengelolaan status belajar pembelajar (misalnya Belum Dimulai, Membaca, Evaluasi, Lulus). |
| Halusinasi | Jawaban AI yang tidak benar atau berada di luar materi kurikulum. |
| Nilai Ambang | Nilai minimal evaluasi agar pembelajar boleh melanjutkan ke modul berikutnya (default 70). |
|   | Acceptance Criteria Kriteria yang harus dipenuhi agar sebuah user story dinyatakan selesai. |
| API | Application Programming Interface. |
| REST | Representational State Transfer, gaya arsitektur API berbasis HTTP. |


| Istilah | Definisi |
| --- | --- |
| UC | Use Case. |

## 1.4 Referensi

- Kerangka Acuan Kerja (KAK) Proyek Pembangunan Virtual Asisten Mentor Edukasi Berbasis Python & AI Model API, Kelompok 8.

- IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications (digantikan oleh ISO/IEC/IEEE 29148:2018, namun kerangkanya masih lazim dipakai sebagai template).

- Sommerville, I. (2016). Software Engineering (10th ed.), Chapter 4.

- Wiegers, K. & Beatty, J. (2013). Software Requirements (3rd ed.), Chapter 10.

- Undang-Undang Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.

- Materi kuliah Proyek SI / PPL Pertemuan 4, FIKSI – UKRI.

## 1.5 Gambaran Umum

Dokumen ini terdiri dari tiga bagian utama dan lampiran. Bagian 1 (Pendahuluan) menjelaskan tujuan, ruang lingkup, istilah, dan referensi. Bagian 2 (Deskripsi Umum) menjelaskan perspektif produk, fungsi, karakteristik pengguna, batasan, dan asumsi, termasuk gambaran use case. Bagian 3 (Kebutuhan Spesifik) memuat antarmuka eksternal, kebutuhan fungsional, use case rinci, kinerja, batasan desain, dan atribut kualitas. Lampiran memuat user story beserta acceptance criteria dan matriks keterlacakan.

Konvensi penulisan: setiap kebutuhan memiliki ID unik (FR-xx untuk fungsional, NFR-xx untuk nonfungsional), memuat satu kebutuhan per kalimat, menggunakan kata “harus”, dan dikaitkan ke tujuan bisnis (BG).


## 2. DESKRIPSI UMUM

## 2.1 Perspektif Produk

Virtual Asisten Mentor Edukasi merupakan produk baru yang berdiri sendiri (standalone) dengan arsitektur klien–server. Backend dibangun dengan Python 3.10 atau lebih baru menggunakan framework FastAPI atau Flask, validasi data memakai Pydantic, serta basis data untuk menyimpan kurikulum, akun, status belajar, dan riwayat percakapan. Sistem berkomunikasi dengan layanan AI Model API pihak ketiga (OpenAI / Anthropic / Local LLM) melalui HTTPS.

Alur umum sistem: pembelajar memilih kurikulum, membaca poin bacaan wajib suatu modul, berdiskusi dengan Mentor AI, mengerjakan evaluasi, dan baru dapat melanjutkan ke modul berikutnya jika lulus.

## 2.2 Fungsi Produk

Fungsi utama produk dirangkum dalam use case berikut. Diagram use case ditampilkan pada Gambar 1 dan rincian fungsi pada Bagian 3.

| ID | Use Case | Aktor | Tujuan Bisnis |
| --- | --- | --- | --- |
|   | UC-01 Registrasi dan Login | Pembelajar, Administrator | BG-04 |
|   | UC-02 Memilih Jalur Belajar | Pembelajar | BG-01 |
|   | UC-03 Membaca Poin Bacaan Wajib | Pembelajar | BG-01 |
|   | UC-04 Berdiskusi dengan Mentor AI | Pembelajar, AI Model API | BG-03 |
|   | UC-05 Mengerjakan Evaluasi Pemahaman | Pembelajar, AI Model API | BG-02, BG-03 |
|   | UC-06 Melanjutkan ke Modul Berikutnya | Pembelajar | BG-02 |
|   | UC-07 Melihat Progres Belajar | Pembelajar | BG-01 |
|   | UC-08 Mengelola Kurikulum dan Poin Bacaan | Administrator | BG-01, BG-04 |
|   | UC-09 Mengatur System Prompt dan Model AI | Administrator | BG-03, BG-04 |


*Gambar 1. Diagram Use Case Sistem Virtual Asisten Mentor Edukasi*

## 2.3 Karakteristik Pengguna

| Pengguna | Karakteristik | Kebutuhan Utama |
| --- | --- | --- |
| Pembelajar | Pelajar atau mahasiswa; pengetahuan teknis dasar; belajar mandiri. | Jalur belajar jelas, penjelasan mudah dipahami, umpan balik cepat. |
| Administrator | Pengelola kurikulum; memahami materi dan dasar teknis sistem. | Mengelola materi, soal, dan konfigurasi AI dengan mudah. |
| AI Model API (sistem eksternal) | Layanan LLM pihak ketiga yang diakses melalui API. | Permintaan terstruktur berisi konteks modul dan System Prompt. |

## 2.4 Batasan

- Pengembangan memakai Python 3.10 atau lebih baru dengan framework FastAPI / Flask dan Pydantic.

- Waktu pengerjaan 30 hari kalender dengan tiga personil (Project Manager / Systems Analyst, Python Backend Developer, AI / Prompt Engineer).

- Sistem bergantung pada ketersediaan dan kuota layanan AI Model API pihak ketiga serta koneksi internet yang stabil.

- Jawaban AI wajib dibatasi pada materi kurikulum yang terdaftar.

- Pengembangan menggunakan pustaka open-source yang legal dan mematuhi standar penulisan kode yang disepakati.


- Lingkungan pengembangan berupa server lokal atau cloud development workspace; keluaran berupa purwarupa (prototype).

- Pengelolaan data pribadi harus sesuai peraturan perlindungan data pribadi di Indonesia.

## 2.5 Asumsi dan Ketergantungan

- Kurikulum dan materi bacaan tersedia, valid, dan terstruktur sebelum pengembangan modul dimulai.

- Penyedia layanan AI API tersedia dan kunci API (API key) dapat diperoleh oleh tim.

- Pembelajar memiliki perangkat dengan peramban modern dan akses internet.

- Perangkat pengembang memiliki RAM minimum 8 GB dengan VS Code, Git, dan Python Environment.

- Bahasa utama materi dan interaksi adalah Bahasa Indonesia.


## 3. KEBUTUHAN SPESIFIK

## 3.1 Antarmuka Eksternal

## 3.1.1 Antarmuka Pengguna

Sistem menyediakan antarmuka berbasis web sederhana (atau antarmuka CLI untuk purwarupa) yang memuat halaman login, daftar kurikulum, halaman poin bacaan, jendela percakapan dengan Mentor AI, halaman evaluasi, halaman progres, dan halaman administrasi.

## 3.1.2 Antarmuka Perangkat Keras

Tidak ada perangkat keras khusus. Server memerlukan CPU dan RAM yang memadai untuk menjalankan aplikasi Python; perangkat klien cukup berupa komputer atau ponsel dengan peramban.

## 3.1.3 Antarmuka Perangkat Lunak

| Komponen | Keterangan |
| --- | --- |
| AI Model API | Layanan LLM (OpenAI / Anthropic / Local LLM) diakses lewat HTTPS dengan format JSON. |
| Basis data | Menyimpan akun, kurikulum, modul, status belajar, nilai, dan riwayat percakapan. |
| Framework backend | FastAPI / Flask dengan validasi Pydantic. |
|   | Sistem operasi server Windows atau Linux yang mendukung Python 3.10 atau lebih baru. |

## 3.1.4 Antarmuka Komunikasi

Komunikasi klien–server dan server–AI API menggunakan protokol HTTPS dengan format data JSON melalui REST API.

## 3.2 Kebutuhan Fungsional

Prioritas: T = Tinggi, S = Sedang, R = Rendah.

| ID | Kebutuhan | Prior. | Use Case | Tujuan Bisnis |
| --- | --- | --- | --- | --- |
|   | FR-01 Sistem harus menyediakan registrasi akun pembelajar. |   | T UC-01 | BG-04 |
|   | FR-02 Sistem harus memverifikasi identitas pengguna melalui login. |   | T UC-01 | BG-04 |
|   | FR-03 Sistem harus menampilkan daftar kurikulum yang tersedia. |   | T UC-02 | BG-01 |
|   | FR-04 Sistem harus membagi setiap kurikulum menjadi modul-modul berurutan. |   | T UC-02 | BG-01 |


| ID | Kebutuhan | Prior. | Use Case | Tujuan Bisnis |
| --- | --- | --- | --- | --- |
|   | FR-05 Sistem harus menampilkan poin bacaan wajib sebelum fitur diskusi dan evaluasi suatu modul dapat diakses. |   | T UC-03 | BG-01 |
|   | FR-06 Sistem harus menyimpan status belajar setiap pembelajar pada setiap modul menggunakan state machine. |   | T UC-03, UC- 06 | BG-02 |
|   | FR-07 Sistem harus menerima pertanyaan pembelajar dalam bentuk teks. |   | T UC-04 | BG-03 |
|   | FR-08 Sistem harus mengirim pertanyaan pembelajar beserta konteks modul dan System Prompt ke AI Model API. |   | T UC-04 | BG-03 |
|   | FR-09 Sistem harus menampilkan penjelasan kontekstual dari Mentor AI. |   | T UC-04 | BG-03 |
|   | FR-10 Sistem harus menyediakan analogi sederhana ketika pembelajar meminta penjelasan yang lebih mudah. |   | S UC-04 | BG-03 |
|   | FR-11 Sistem harus membuat soal evaluasi berdasarkan poin bacaan wajib modul yang sedang dipelajari. |   | T UC-05 | BG-02, BG- 03 |
|   | FR-12 Sistem harus menilai jawaban pembelajar dan menghasilkan nilai evaluasi. |   | T UC-05 | BG-03 |
|   | FR-13 Sistem harus memberikan umpan balik pada setiap jawaban evaluasi. |   | S UC-05 | BG-03 |
|   | FR-14 Sistem harus mengizinkan akses ke modul berikutnya hanya jika nilai evaluasi mencapai nilai ambang. |   | T UC-06 | BG-02 |
|   | FR-15 Sistem harus mengarahkan pembelajar mengulang modul jika nilai evaluasi di bawah nilai ambang. |   | T UC-06 | BG-02 |
|   | FR-16 Sistem harus menampilkan progres belajar berupa persentase modul yang telah lulus. |   | S UC-07 | BG-01 |
|   | FR-17 Sistem harus menolak pertanyaan yang berada di luar materi kurikulum. |   | T UC-04 | BG-04 |
|   | FR-18 Sistem harus menyimpan riwayat percakapan setiap pembelajar. |   | S UC-04 | BG-03 |


| ID | Kebutuhan | Prior. | Use Case | Tujuan Bisnis |
| --- | --- | --- | --- | --- |
|   | FR-19 Administrator harus dapat menambah, mengubah, dan menghapus kurikulum, modul, dan poin bacaan wajib. |   | T UC-08 | BG-01, BG- 04 |
|   | FR-20 Administrator harus dapat mengubah System Prompt dan memilih model AI yang digunakan. |   | S UC-09 | BG-03 |
|   | FR-21 Sistem harus menampilkan pesan kesalahan yang jelas ketika AI Model API tidak dapat dihubungi. |   | T UC-04, UC- 05 | BG-04 |
|   | FR-22 Sistem harus menyediakan REST API yang terdokumentasi untuk seluruh fungsi utama. | S | Semua UC BG-04 |   |

## 3.3 Spesifikasi Use Case

Tiga use case berikut diuraikan secara rinci karena merupakan inti proses mentoring. Use case lain mengikuti pola serupa dan dapat dirinci pada tahap perancangan.

## UC-04 Berdiskusi dengan Mentor AI

| ID | UC-04 |
| --- | --- |
| Nama | Berdiskusi dengan Mentor AI |
| Aktor | Pembelajar (aktor utama); AI Model API (aktor pendukung) |
| Deskripsi | Pembelajar mengajukan pertanyaan tentang modul dan menerima penjelasan kontekstual dari Mentor AI. |
| Prakondisi | Pembelajar sudah login dan sudah membuka poin bacaan wajib modul (FR-05). |
| Alur Utama | 1. Pembelajar menulis pertanyaan pada jendela percakapan. 2. Sistem memvalidasi bahwa pertanyaan tidak kosong. 3. Sistem mengirim pertanyaan, konteks modul, dan System Prompt ke AI Model API. 4. AI Model API mengembalikan jawaban. 5. Sistem memeriksa bahwa jawaban sesuai materi modul. 6. Sistem menampilkan jawaban dan menyimpan riwayat percakapan. |


| Alur Alternatif | A1. Pertanyaan di luar kurikulum: sistem menolak dan mengarahkan pembelajar kembali ke materi (FR-17). A2. Pembelajar meminta penjelasan lebih sederhana: sistem meminta AI memberikan analogi (FR-10). A3. AI Model API gagal merespons: sistem menampilkan pesan kesalahan dan menawarkan percobaan ulang (FR-21). |
| --- | --- |
| Pascakondisi | Pertanyaan dan jawaban tersimpan pada riwayat percakapan. |

## UC-05 Mengerjakan Evaluasi Pemahaman

| ID | UC-05 |
| --- | --- |
| Nama | Mengerjakan Evaluasi Pemahaman |
| Aktor | Pembelajar (aktor utama); AI Model API (aktor pendukung) |
| Deskripsi | Pembelajar menjawab soal evaluasi modul dan menerima nilai serta umpan balik. |
| Prakondisi | Pembelajar sudah membaca poin bacaan wajib modul dan status modul adalah “Membaca”. |
| Alur Utama | 1. Pembelajar memilih tombol mulai evaluasi. 2. Sistem membuat soal berdasarkan poin bacaan wajib (FR-11). 3. Pembelajar menjawab seluruh soal dan mengirim jawaban. 4. Sistem menilai jawaban dengan bantuan AI Model API (FR-12). 5. Sistem menampilkan nilai dan umpan balik tiap soal (FR-13). 6. Sistem memperbarui status modul. |
| Alur Alternatif | A1. Ada soal belum dijawab: sistem meminta pembelajar melengkapi jawaban. A2. AI Model API gagal: sistem menyimpan jawaban dan meminta pembelajar mengirim ulang (FR-21). |
| Pascakondisi | Nilai evaluasi dan status modul tersimpan. |

## UC-06 Melanjutkan ke Modul Berikutnya

| ID | UC-06 |
| --- | --- |
| Nama | Melanjutkan ke Modul Berikutnya |
| Aktor | Pembelajar |
| Deskripsi | Sistem membuka modul berikutnya hanya jika pembelajar lulus evaluasi modul sebelumnya. |
| Prakondisi | Pembelajar telah menyelesaikan UC-05 untuk modul saat ini. |


| Alur Utama | 1. Pembelajar memilih tombol lanjut ke modul berikutnya. 2. Sistem memeriksa nilai evaluasi terhadap nilai ambang (FR-14). 3. Sistem mengubah status modul saat ini menjadi “Lulus”. 4. Sistem membuka modul berikutnya dan menampilkan poin bacaan wajibnya. |
| --- | --- |
| Alur Alternatif | A1. Nilai di bawah ambang: sistem menolak akses dan mengarahkan pembelajar mengulang modul (FR-15). A2. Tidak ada modul berikutnya: sistem menampilkan pesan kurikulum selesai. |
| Pascakondisi | Status belajar pembelajar diperbarui. |

## 3.4 Kebutuhan Kinerja

| ID | Kebutuhan | Tujuan Bisnis |
| --- | --- | --- |
|   | NFR-01 Sistem harus merespons permintaan non-AI dalam waktu paling lama 2 detik untuk 95% permintaan. | BG-04 |
|   | NFR-02 Sistem harus menampilkan jawaban Mentor AI dalam waktu paling lama 10 detik untuk 90% permintaan. | BG-03 |
|   | NFR-03 Sistem harus melayani minimal 50 pengguna secara bersamaan tanpa penurunan kinerja di luar batas NFR-01 dan NFR-02. | BG-04 |
|   | NFR-04 Sistem harus mencapai ketersediaan minimal 99% selama masa pengujian 7 hari. | BG-04 |

## 3.5 Batasan Desain

| ID | Batasan | Sumber KAK |
| --- | --- | --- |
|   | NFR-05 Sistem harus dikembangkan menggunakan Python versi 3.10 atau lebih baru. | II.2 |
|   | NFR-06 Sistem harus menggunakan FastAPI atau Flask sebagai framework backend. | II.2 |
|   | NFR-07 Sistem harus menggunakan Pydantic untuk validasi data masuk dan keluar. | II.2 |
|   | NFR-08 Sistem harus menyimpan kunci API pada variabel lingkungan dan tidak menuliskannya pada kode sumber. | IV |
|   | NFR-09 Sistem harus menggunakan pustaka open-source berlisensi legal. | IV |


## 3.6 Atribut Kualitas

| ID | Atribut | Kebutuhan (terukur) | Tujuan Bisnis |
| --- | --- | --- | --- |
|   | NFR-10 Keamanan | Sistem harus menyimpan kata sandi dalam bentuk hash (misalnya bcrypt), tidak sebagai teks biasa. | BG-04 |
|   | NFR-11 Keamanan | Sistem harus mengenkripsi seluruh komunikasi menggunakan TLS versi 1.2 atau lebih baru. | BG-04 |
| NFR-12 Privasi |   | Sistem harus mematuhi UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi dengan hanya menyimpan data pribadi yang diperlukan. | BG-04 |
| NFR-13 Akurasi |   | Mentor AI harus menjawab sesuai materi kurikulum pada minimal 90% dari 50 pertanyaan uji, dengan halusinasi maksimal 10%. | BG-04 |
|   | NFR-14 Kemudahan penggunaan | Minimal 80% pengguna uji harus dapat menyelesaikan satu modul tanpa bantuan, dengan skor SUS minimal 68. | BG-02 |
|   | NFR-15 Keandalan | Sistem harus tetap berjalan dan menampilkan pesan kesalahan yang jelas pada 100% kasus kegagalan AI API yang diuji. | BG-04 |
|   | NFR-16 Pemeliharaan | Kode program harus mengikuti PEP 8 dan memiliki cakupan pengujian unit minimal 70%. | BG-04 |
|   | NFR-17 Portabilitas | Penyedia model AI harus dapat diganti hanya melalui perubahan konfigurasi tanpa mengubah logika inti. | BG-03 |
|   | NFR-18 Dokumentasi | Tim harus menyerahkan dokumentasi kode, dokumentasi API, dan panduan penggunaan pada akhir proyek. | BG-04 |


## LAMPIRAN A. USER STORY DAN ACCEPTANCE CRITERIA

US-01 (UC-03, FR-05)

User story: Sebagai pembelajar, saya ingin membaca poin bacaan wajib terlebih dahulu agar saya memahami garis besar materi sebelum berdiskusi.

## Acceptance criteria:

- Poin bacaan wajib tampil sebelum tombol diskusi dan evaluasi aktif.

- Poin bacaan dapat dibuka tanpa kesalahan dalam 2 detik.

- Status modul berubah menjadi “Membaca” setelah poin dibuka.

## US-02 (UC-04, FR-09)

User story: Sebagai pembelajar, saya ingin bertanya kepada Mentor AI agar materi yang belum jelas dapat dijelaskan sesuai konteks modul.

## Acceptance criteria:

- Jawaban muncul dalam maksimal 10 detik pada 90% percobaan.

- Jawaban hanya membahas materi modul yang sedang dipelajari.

- Pertanyaan di luar kurikulum ditolak dengan pesan arahan kembali ke materi.

## US-03 (UC-05, FR-12)

User story: Sebagai pembelajar, saya ingin mengerjakan evaluasi agar saya mengetahui sejauh mana pemahaman saya.

## Acceptance criteria:

- Soal dibuat dari poin bacaan wajib modul terkait.

- Nilai dan umpan balik tampil setelah seluruh jawaban dikirim.

- Hasil evaluasi tersimpan dan dapat dilihat kembali.

## US-04 (UC-06, FR-14)

User story: Sebagai pembelajar, saya ingin diizinkan lanjut hanya setelah lulus agar jalur belajar saya terarah.

## Acceptance criteria:

- Modul berikutnya terkunci jika nilai di bawah 70.

- Modul berikutnya terbuka otomatis jika nilai minimal 70.

- Pembelajar yang tidak lulus mendapat arahan mengulang modul.

## US-05 (UC-08, FR-19)

User story: Sebagai administrator, saya ingin mengelola kurikulum dan poin bacaan agar materi selalu valid dan terbaru.

## Acceptance criteria:

- Administrator dapat menambah, mengubah, dan menghapus modul.


- Perubahan tampil pada pembelajar tanpa menjalankan ulang sistem.

- Pengguna non-administrator tidak dapat mengakses halaman pengelolaan.

## LAMPIRAN B. MATRIKS KETERLACAKAN

Matriks berikut menunjukkan keterkaitan setiap tujuan bisnis dengan use case dan kebutuhan.

| Tujuan Bisnis | Use Case | Kebutuhan |
| --- | --- | --- |
|   | BG-01 UC-02, UC-03, UC- 07, UC-08 | FR-03, FR-04, FR-05, FR-16, FR-19 |
|   | BG-02 UC-05, UC-06 | FR-06, FR-11, FR-14, FR-15, NFR-14 |
|   | BG-03 UC-04, UC-05, UC- 09 | FR-07 s.d. FR-13, FR-18, FR-20, NFR-02, NFR-17 |
|   | BG-04 UC-01, UC-08, UC- 09 | FR-01, FR-02, FR-17, FR-21, FR-22, NFR-01, NFR-03 s.d. NFR-13, NFR-15, NFR-16, NFR-18 |

Disetujui oleh,

(Project Manager / Systems Analyst)
