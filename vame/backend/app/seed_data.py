"""Data awal kurikulum (SRS 1.4: Python, Logika Pemrograman, Analisis Sistem).
Bentuknya sama dengan format impor JSON `POST /api/v1/curricula/import` (FR-09).
Seluruh materi ditulis ringkas untuk purwarupa dan mencantumkan sumber rujukan (BR-05)."""

PY_REF = "The Python Tutorial - Python Software Foundation (docs.python.org/3/tutorial)"


def rp(order, title, objective, keywords, content, ref=PY_REF):
    return {"order": order, "title": title, "objective": objective, "keywords": keywords, "content": content.strip(), "references": ref}


PYTHON = {
    "code": "PY-ALG-101",
    "title": "Dasar Pemrograman Python & Logika Algoritma",
    "short_name": "Python & Algoritma",
    "description": "Kuasai sintaksis dasar, manipulasi memori, struktur kontrol percabangan, algoritma perulangan, hingga modularitas kode dengan panduan interaktif dari AI Mentor tersertifikasi.",
    "level": "Dasar",
    "topic_label": "Python 3.12",
    "est_hours": 18,
    "mentor_name": "Tutor AI VAME v4.2",
    "modules": [
        {
            "order": 1, "title": "Pengenalan & Sintaks Dasar Python", "label": "MODUL FONDASI",
            "reading_points": [
                rp(1, "Apa itu Python & Interpreter", "Menjelaskan fungsi interpreter, indentasi, komentar, dan print().",
                   ["interpreter", "indentasi", "komentar", "print", "REPL"],
                   '''
Python adalah bahasa pemrograman tingkat tinggi yang dijalankan baris demi baris oleh interpreter. Kamu bisa menulis kode di berkas berekstensi .py atau mengetik langsung di REPL (mode interaktif).
Python memakai indentasi, yaitu spasi di awal baris, untuk menandai satu blok kode. Berbeda dengan bahasa yang memakai kurung kurawal, indentasi di Python wajib konsisten, biasanya 4 spasi.
Komentar diawali tanda # dan diabaikan interpreter; gunakan untuk menjelaskan maksud kode. Fungsi print() menampilkan keluaran ke layar.

```python
# ini komentar
print("Halo, VAME!")
```
Analogi: interpreter seperti penerjemah simultan yang menerjemahkan dan menyampaikan satu kalimat sekaligus kepada komputer.
'''),
                rp(2, "Variabel & Tipe Data Dasar", "Membuat variabel dan mengenali tipe data int, float, str, bool.",
                   ["variabel", "int", "float", "str", "bool", "tipe dinamis"],
                   '''
Variabel adalah nama yang menunjuk ke sebuah nilai di memori. Variabel dibuat dengan tanda sama dengan (=) tanpa perlu menyatakan tipenya, karena Python bertipe dinamis.
Analogi: variabel seperti label pada kotak; kotaknya berisi nilai, labelnya adalah nama variabel.
Empat tipe data dasar adalah int (bilangan bulat), float (bilangan desimal), str (teks), dan bool (True atau False). Fungsi type() menampilkan tipe suatu nilai.

```python
umur = 20          # int
tinggi = 1.7       # float
nama = "Budi"      # str
aktif = True       # bool
print(type(umur))  # <class 'int'>
```
Nama variabel peka huruf besar-kecil dan tidak boleh diawali angka.
'''),
                rp(3, "Input, Output & Operator Aritmetika", "Membaca input, mengonversi tipe, dan memakai operator aritmetika serta f-string.",
                   ["input", "konversi tipe", "operator aritmetika", "f-string", "modulus"],
                   '''
Fungsi input() membaca teks dari pengguna dan selalu menghasilkan str. Untuk menghitung, ubah dulu dengan int() atau float(); ini disebut konversi tipe.
Operator aritmetika: + (tambah), - (kurang), * (kali), / (bagi, hasil float), // (bagi bulat), % (modulus atau sisa bagi), dan ** (pangkat).
f-string memudahkan menyisipkan variabel ke teks dengan awalan f dan kurung kurawal.

```python
a = int(input("Angka: "))
print(f"{a} dibagi 3 = {a // 3} sisa {a % 3}")
```
Modulus berguna misalnya untuk memeriksa bilangan genap: a % 2 == 0.
'''),
            ],
        },
        {
            "order": 2, "title": "Struktur Kontrol Alur & Percabangan", "label": "MODUL STRUKTUR",
            "reading_points": [
                rp(1, "Boolean & Operator Logika", "Menyusun ekspresi boolean dengan operator perbandingan dan and, or, not.",
                   ["boolean", "operator perbandingan", "and", "or", "not", "short-circuit"],
                   '''
Nilai boolean hanya True atau False. Operator perbandingan menghasilkan boolean: == (sama dengan), != (tidak sama), <, >, <=, dan >=. Jangan tertukar: = adalah penugasan nilai, sedangkan == adalah perbandingan.
Operator logika menggabungkan boolean: and bernilai True jika kedua sisi True; or bernilai True jika salah satu True; not membalik nilai.
Python memakai short-circuit: pada "A and B", jika A sudah False maka B tidak dievaluasi; pada "A or B", jika A sudah True maka B tidak dievaluasi.

```python
umur = 20
punya_ktp = True
print(umur >= 17 and punya_ktp)   # True
print(not punya_ktp)              # False
```
'''),
                rp(2, "Percabangan if, elif, else", "Menulis percabangan if-elif-else dengan indentasi yang benar.",
                   ["if", "elif", "else", "kondisi", "indentasi"],
                   '''
Percabangan memungkinkan program memilih jalur berdasarkan kondisi. Kata kunci if menjalankan blok jika kondisinya True. elif (else if) memeriksa kondisi lain bila yang sebelumnya False, dan else dijalankan bila semua kondisi False.
Kondisi diakhiri titik dua (:) dan blok di bawahnya harus menjorok (indentasi). Hanya satu blok yang dijalankan, yaitu blok pertama yang kondisinya True.

```python
nilai = 82
if nilai >= 85:
    grade = "A"
elif nilai >= 70:
    grade = "B"
else:
    grade = "C"
print(grade)  # B
```
Urutan elif penting: kondisi yang lebih ketat diletakkan lebih dulu.
'''),
                rp(3, "Percabangan Bersarang & Ekspresi Kondisional", "Memakai nested if, ekspresi kondisional satu baris, serta konsep truthy dan falsy.",
                   ["nested if", "ekspresi kondisional", "truthy", "falsy"],
                   '''
Nested if adalah if di dalam if, dipakai ketika satu keputusan bergantung pada keputusan lain. Hindari sarang terlalu dalam karena sulit dibaca; sering kali bisa disederhanakan dengan operator and.
Ekspresi kondisional menulis pilihan sederhana dalam satu baris: nilai_jika_benar if kondisi else nilai_jika_salah.
Dalam kondisi, Python menganggap beberapa nilai sebagai falsy: 0, 0.0, string kosong "", list kosong [], dan None. Nilai lainnya truthy.

```python
umur = 17
status = "dewasa" if umur >= 18 else "belum dewasa"
if "":
    print("tidak tercetak")  # string kosong falsy
```
'''),
            ],
        },
        {
            "order": 3, "title": "Perulangan (Looping)", "label": "MODUL PERULANGAN",
            "reading_points": [
                rp(1, "Perulangan for & range()", "Menjalankan perulangan for dengan range() dan iterasi urutan.",
                   ["for", "range", "iterasi", "variabel penghitung"],
                   '''
Perulangan for mengulang blok kode untuk setiap elemen dalam suatu urutan. range(n) menghasilkan bilangan 0 sampai n-1; range(awal, akhir, langkah) memberi kontrol lebih. Nilai akhir tidak ikut dihitung.
Setiap putaran disebut iterasi, dan variabel perulangan (mis. i) menyimpan nilai saat itu.

```python
total = 0
for i in range(1, 6):   # 1,2,3,4,5
    total += i
print(total)            # 15
```
Gunakan for bila jumlah pengulangan diketahui atau ada kumpulan data yang ditelusuri.
'''),
                rp(2, "Perulangan while, break & continue", "Memakai while dengan kondisi berhenti serta break dan continue.",
                   ["while", "break", "continue", "kondisi berhenti", "loop tak hingga"],
                   '''
Perulangan while mengulang selama kondisinya True, cocok bila jumlah pengulangan belum diketahui. Pastikan ada sesuatu yang mengubah kondisi agar akhirnya False; jika tidak, terjadi loop tak hingga.
break menghentikan perulangan seketika, sedangkan continue melompat ke iterasi berikutnya tanpa menjalankan sisa blok.

```python
n = 0
while True:
    n += 1
    if n % 2 == 0:
        continue      # lewati bilangan genap
    if n > 7:
        break         # berhenti
    print(n)          # 1 3 5 7
```
'''),
            ],
        },
        {
            "order": 4, "title": "Struktur Data Dasar", "label": "MODUL DATA",
            "reading_points": [
                rp(1, "List & Tuple", "Membedakan list (mutable) dan tuple (immutable) serta operasi dasarnya.",
                   ["list", "tuple", "indeks", "mutable", "immutable", "slicing"],
                   '''
List adalah kumpulan nilai berurutan yang ditulis dengan kurung siku dan dapat diubah (mutable). Elemen diakses dengan indeks yang dimulai dari 0; indeks negatif menghitung dari belakang. Slicing [a:b] mengambil sebagian elemen.
Tuple mirip list tetapi ditulis dengan kurung biasa dan tidak dapat diubah (immutable), cocok untuk data tetap seperti koordinat.

```python
buah = ["apel", "jeruk", "mangga"]
buah.append("pisang")
print(buah[0], buah[-1])   # apel pisang
titik = (3, 4)             # tuple
```
Metode umum list: append(), remove(), pop(), dan len() untuk menghitung jumlah elemen.
'''),
                rp(2, "Dictionary & Set", "Memakai dictionary berpasangan kunci-nilai dan set untuk data unik.",
                   ["dictionary", "kunci", "nilai", "set", "unik"],
                   '''
Dictionary menyimpan pasangan kunci-nilai dengan kurung kurawal dan diakses lewat kuncinya, bukan indeks. Kunci harus unik. Analogi: kamus, kata (kunci) menuju arti (nilai).
Set adalah kumpulan elemen unik tanpa urutan; duplikat otomatis dibuang, berguna untuk menghilangkan data ganda.

```python
siswa = {"nama": "Budi", "nilai": 90}
siswa["kelas"] = "X-A"
print(siswa["nama"])        # Budi
angka = set([1, 2, 2, 3])   # {1, 2, 3}
```
Gunakan .get(kunci) untuk membaca kunci yang mungkin tidak ada tanpa memunculkan galat.
'''),
            ],
        },
        {
            "order": 5, "title": "Fungsi & Modularitas", "label": "MODUL FUNGSI",
            "reading_points": [
                rp(1, "Mendefinisikan Fungsi", "Menulis fungsi dengan parameter dan nilai kembalian (return).",
                   ["def", "parameter", "argumen", "return", "scope"],
                   '''
Fungsi adalah blok kode bernama yang dapat dipanggil berulang kali, sehingga kode lebih rapi dan tidak berulang. Fungsi dibuat dengan kata kunci def, memiliki parameter sebagai masukan, dan return untuk mengembalikan hasil.
Nilai yang dikirim saat memanggil disebut argumen. Variabel yang dibuat di dalam fungsi bersifat lokal (scope lokal) dan tidak terlihat dari luar.

```python
def luas_persegi(sisi):
    return sisi * sisi

print(luas_persegi(5))   # 25
```
Fungsi tanpa return mengembalikan None.
'''),
                rp(2, "Modul & Import", "Memakai import untuk memanfaatkan modul standar dan memecah kode ke berkas.",
                   ["modul", "import", "from import", "pustaka standar"],
                   '''
Modul adalah berkas Python berisi fungsi dan variabel yang bisa dipakai ulang. Gunakan import untuk memuatnya. Python punya pustaka standar seperti math dan random.
import nama_modul memuat seluruh modul (diakses dengan nama_modul.fungsi), sedangkan from nama_modul import fungsi memuat bagian tertentu saja.

```python
import math
from random import randint
print(math.sqrt(16))     # 4.0
print(randint(1, 6))
```
Memecah program menjadi beberapa modul disebut modularitas; kode jadi lebih mudah dirawat dan diuji.
'''),
            ],
        },
        {
            "order": 6, "title": "Algoritma Dasar: Pencarian & Pengurutan", "label": "MODUL ALGORITMA",
            "reading_points": [
                rp(1, "Pencarian Linear (Linear Search)", "Menjelaskan dan menulis algoritma linear search beserta kelemahannya.",
                   ["linear search", "algoritma", "kompleksitas", "indeks"],
                   '''
Linear search mencari nilai dengan memeriksa elemen satu per satu dari awal sampai ketemu atau data habis. Algoritma ini sederhana dan bekerja pada data tidak terurut, tetapi pada kasus terburuk harus memeriksa semua elemen, sehingga waktunya bertambah sebanding jumlah data (O(n)).

```python
def cari(data, target):
    for i, nilai in enumerate(data):
        if nilai == target:
            return i      # indeks ditemukan
    return -1             # tidak ada
print(cari([4, 8, 15], 8))   # 1
```
Analogi: mencari nama di daftar hadir dengan menelusuri dari baris pertama.
''', ref="Python Tutorial & Algoritma dasar (docs.python.org/3/tutorial/controlflow.html)"),
                rp(2, "Pengurutan Sederhana: Bubble Sort", "Menjelaskan cara kerja bubble sort dan alasan ia kurang efisien untuk data besar.",
                   ["bubble sort", "pengurutan", "pertukaran", "perbandingan", "O(n^2)"],
                   '''
Bubble sort mengurutkan data dengan membandingkan dua elemen bersebelahan dan menukarnya jika urutannya salah; proses diulang hingga tidak ada pertukaran lagi. Elemen terbesar "menggelembung" ke ujung pada tiap putaran.
Karena memakai dua perulangan bersarang, waktunya sekitar O(n^2), sehingga lambat untuk data besar. Pada praktik, gunakan sorted() atau .sort() bawaan Python.

```python
def bubble(data):
    n = len(data)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data
print(bubble([5, 2, 9, 1]))   # [1, 2, 5, 9]
```
''', ref="Python Tutorial & Algoritma dasar (docs.python.org/3/howto/sorting.html)"),
            ],
        },
    ],
}

LOGIKA = {
    "code": "LOG-PRG-101",
    "title": "Logika Pemrograman & Berpikir Algoritmik",
    "short_name": "Logika Pemrograman",
    "description": "Melatih cara berpikir sistematis: memahami algoritma, flowchart, pseudocode, dan memecah masalah menjadi langkah-langkah kecil.",
    "level": "Dasar",
    "topic_label": "Algoritma",
    "est_hours": 6,
    "mentor_name": "Tutor AI VAME v4.2",
    "modules": [
        {
            "order": 1, "title": "Berpikir Algoritmik", "label": "MODUL FONDASI",
            "reading_points": [
                rp(1, "Algoritma & Flowchart", "Menjelaskan ciri algoritma dan simbol dasar flowchart.",
                   ["algoritma", "flowchart", "input", "proses", "output", "terminator"],
                   '''
Algoritma adalah urutan langkah yang jelas dan terbatas untuk menyelesaikan suatu masalah. Ciri algoritma yang baik: memiliki input, proses, dan output; setiap langkah jelas (tidak ambigu); dan akhirnya berhenti.
Flowchart menggambarkan algoritma dengan simbol: oval (terminator) untuk mulai/selesai, jajar genjang untuk input/output, persegi panjang untuk proses, dan belah ketupat untuk keputusan (ya/tidak).
Contoh: algoritma membuat teh: panaskan air (proses), masukkan teh (proses), tuang ke gelas (output).
''', ref="Materi Dasar Algoritma & Pemrograman (rujukan internal VAME)"),
                rp(2, "Pseudocode & Dekomposisi Masalah", "Menulis pseudocode dan memecah masalah besar menjadi sub-masalah.",
                   ["pseudocode", "dekomposisi", "sub-masalah", "urutan", "percabangan", "perulangan"],
                   '''
Pseudocode adalah penulisan algoritma dengan bahasa mirip kode tetapi tidak terikat sintaks bahasa tertentu, sehingga fokus pada logika. Tiga struktur dasar: urutan, percabangan (JIKA...MAKA...), dan perulangan (ULANGI...).
Dekomposisi adalah memecah masalah besar menjadi sub-masalah kecil yang lebih mudah diselesaikan, lalu menggabungkan hasilnya.

```
MULAI
  BACA nilai
  JIKA nilai >= 70 MAKA TULIS "Lulus"
  SELAIN ITU TULIS "Belum lulus"
SELESAI
```
''', ref="Materi Dasar Algoritma & Pemrograman (rujukan internal VAME)"),
            ],
        }
    ],
}

SISTEM = {
    "code": "SYS-ANL-101",
    "title": "Dasar Analisis Sistem Informasi",
    "short_name": "Analisis Sistem",
    "description": "Pengantar analisis sistem: siklus hidup pengembangan sistem dan cara merumuskan kebutuhan fungsional serta nonfungsional.",
    "level": "Dasar",
    "topic_label": "Rekayasa Sistem",
    "est_hours": 6,
    "mentor_name": "Tutor AI VAME v4.2",
    "modules": [
        {
            "order": 1, "title": "Dasar Analisis Sistem", "label": "MODUL FONDASI",
            "reading_points": [
                rp(1, "Siklus Hidup Pengembangan Sistem (SDLC)", "Menyebutkan tahapan SDLC dan tujuan tiap tahap.",
                   ["SDLC", "analisis", "perancangan", "implementasi", "pengujian", "pemeliharaan"],
                   '''
SDLC (System Development Life Cycle) adalah tahapan terstruktur membangun sistem informasi. Tahap umumnya: perencanaan, analisis kebutuhan, perancangan, implementasi (pengodean), pengujian, penerapan, dan pemeliharaan.
Analisis menentukan apa yang dibutuhkan pengguna; perancangan menentukan bagaimana sistem dibangun; pengujian memastikan sistem sesuai kebutuhan. Model yang umum dipakai antara lain waterfall (berurutan) dan iteratif/agile (bertahap).
''', ref="Rekayasa Perangkat Lunak - materi pengantar (rujukan internal VAME)"),
                rp(2, "Kebutuhan Fungsional & Nonfungsional", "Membedakan kebutuhan fungsional dan nonfungsional dengan contoh.",
                   ["kebutuhan fungsional", "kebutuhan nonfungsional", "SRS", "performa", "keamanan"],
                   '''
Kebutuhan fungsional menjelaskan apa yang harus dilakukan sistem, misalnya "sistem menyediakan login pengguna". Kebutuhan nonfungsional menjelaskan mutu sistem, misalnya kecepatan respons, keamanan, kemudahan penggunaan, dan keandalan.
Keduanya dituliskan dalam dokumen SRS (Software Requirements Specification) agar menjadi kesepakatan antara pengguna dan pengembang, serta dasar pengujian. Kebutuhan yang baik jelas, dapat diuji, dan tidak ambigu.
''', ref="Rekayasa Perangkat Lunak - materi pengantar (rujukan internal VAME)"),
            ],
        }
    ],
}

ALL_CURRICULA = [PYTHON, LOGIKA, SISTEM]
