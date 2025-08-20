# 💰 Telegram Finance Bot

Bot Telegram untuk pencatatan keuangan yang terintegrasi dengan Google Spreadsheet dan AI Assistant (Gemini) untuk membantu mengelola keuangan pribadi dan analisis finansial.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)

## ✨ Fitur Utama

- 💰 **Pencatatan Transaksi**: Catat pemasukan dan pengeluaran dengan mudah
- 📊 **Integrasi Google Sheets**: Data tersimpan otomatis di Google Spreadsheet
- 🤖 **AI Assistant**: Analisis keuangan dan saran finansial dengan Gemini AI
- 📈 **Laporan Keuangan**: Laporan harian, mingguan, dan bulanan
- 🏷️ **Kategorisasi**: Kategorisasi otomatis transaksi
- 💬 **Natural Language**: Input transaksi dengan bahasa sehari-hari
- 🔍 **Pencarian**: Cari transaksi berdasarkan kategori, tanggal, atau nominal
- 📱 **Multi-User**: Mendukung multiple users dengan spreadsheet terpisah

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/telegram-finance-bot.git
cd telegram-finance-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 4. Run Setup Script
```bash
python setup.py
```

### 5. Start Bot
```bash
python main.py
```

## 📋 Prerequisites

- ✅ Python 3.8 atau lebih baru
- ✅ Akun Google dengan akses Google Sheets
- ✅ Bot Telegram (dari @BotFather)
- ✅ API Key Gemini (Google AI)
- ✅ Koneksi internet stabil

## 🔧 Setup Lengkap

### Langkah 1: Setup Bot Telegram

1. **Buat Bot Baru**:
   - Buka [@BotFather](https://t.me/BotFather) di Telegram
   - Ketik `/newbot`
   - Ikuti instruksi untuk membuat bot
   - Simpan token yang diberikan

2. **Setup Commands** (Optional):
   ```
   start - Menu utama
   help - Bantuan penggunaan
   income - Tambah pemasukan
   expense - Tambah pengeluaran
   report - Lihat laporan keuangan
   search - Cari transaksi
   ai - Chat dengan AI Assistant
   balance - Cek saldo
   categories - Kelola kategori
   ```

### Langkah 2: Setup Google Sheets API

1. **Buat Project di Google Cloud Console**
   - Buka [Google Cloud Console](https://console.cloud.google.com)
   - Klik "Create Project"
   - Beri nama project

2. **Enable Google Sheets API**
   - Di dashboard, klik "Enable APIs and Services"
   - Cari "Google Sheets API"
   - Klik dan enable

3. **Buat OAuth 2.0 Credentials**
   - Pergi ke "APIs & Services" > "Credentials"
   - Klik "Create Credentials" > "OAuth client ID"
   - Pilih "Desktop app"
   - Download JSON file
   - Rename menjadi `credentials.json`

### Langkah 3: Setup Gemini API

1. **Buka [Google AI Studio](https://ai.google.dev/)**
2. **Create API Key**
3. **Copy API key yang diberikan**

### Langkah 4: Konfigurasi Environment

Edit file `.env`:
```env
# Bot Telegram Token
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# API Key Gemini
GEMINI_API_KEY=YOUR_GEMINI_KEY_HERE

# Timezone
TIMEZONE=Asia/Jakarta

# Currency
CURRENCY=IDR
```

### Langkah 5: First Run

```bash
python main.py
```

Pada run pertama:
- Browser akan terbuka untuk authorization Google
- Login dengan akun Google Anda
- Allow permissions untuk Google Sheets
- File `token.json` akan dibuat otomatis

## 📱 Cara Penggunaan

### 🎯 Quick Start
1. Kirim `/start` ke bot
2. Bot akan membuat spreadsheet keuangan untuk Anda
3. Mulai catat transaksi

### 📝 Perintah Tersedia

| Command | Deskripsi |
|---------|-----------|
| `/start` | Menu utama dan setup initial |
| `/help` | Panduan penggunaan |
| `/income` | Tambah pemasukan |
| `/expense` | Tambah pengeluaran |
| `/report` | Lihat laporan keuangan |
| `/search` | Cari transaksi |
| `/ai [pesan]` | Chat dengan AI Assistant |
| `/balance` | Cek saldo terkini |
| `/categories` | Kelola kategori |

### 💬 Contoh Penggunaan

**1. Input Transaksi Natural Language:**
```
"Beli groceries 150000"
"Gaji november 8500000"
"Makan di restaurant 75000"
"Bayar internet 350000"
```

**2. Menggunakan AI Assistant:**
```
/ai analisis pengeluaran saya bulan ini
/ai berikan tips hemat untuk kategori makanan
/ai prediksi apakah saya bisa menabung 1 juta bulan ini
```

**3. Laporan Keuangan:**
```
/report - Laporan bulan ini
/report weekly - Laporan minggu ini
/report daily - Laporan hari ini
```

## 📊 Struktur Project

```
telegram-finance-bot/
├── .env                      # Environment variables
├── credentials.json          # Google OAuth credentials
├── main.py                  # Main application
├── config.py                # Configuration settings
├── requirements.txt         # Dependencies
├── setup.py                 # Setup script
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # Command handlers
│   └── keyboards.py         # Keyboard layouts
├── services/
│   ├── __init__.py
│   ├── google_sheets.py     # Google Sheets service
│   └── gemini_ai.py         # AI service
├── utils/
│   ├── __init__.py
│   └── helpers.py           # Helper functions
└── data/
    └── categories.json      # Default categories
```

## 🔧 Troubleshooting

### ❌ Error: "Sheets belum terhubung"
**Solusi:**
- Pastikan file `credentials.json` ada
- Check Google Sheets API sudah enabled
- Jalankan `/start` untuk reconnect

### ❌ Error saat authorization Google
**Solusi:**
- Delete file `token.json`
- Restart bot
- Ulangi proses authorization

### ❌ Bot tidak merespon
**Solusi:**
- Check token bot di `.env`
- Pastikan format token benar
- Check koneksi internet

### ❌ AI tidak berfungsi
**Solusi:**
- Check Gemini API key di `.env`
- Pastikan API key valid
- Check quota API

## 📊 Format Data Google Sheets

### Sheet "Transactions"
| Tanggal | Waktu | Kategori | Deskripsi | Pemasukan | Pengeluaran | Saldo |
|---------|-------|----------|-----------|-----------|-------------|-------|
| 2024-12-25 | 10:30:00 | Gaji | Gaji November | 8,500,000 | | 8,500,000 |
| 2024-12-25 | 14:15:00 | Makanan | Beli groceries | | 150,000 | 8,350,000 |

### Sheet "Categories"
| Kategori | Type | Keywords | Icon |
|----------|------|----------|------|
| Makanan | expense | makan,groceries,restaurant | 🍽️ |
| Transport | expense | bensin,parkir,grab | 🚗 |

### Sheet "Monthly_Summary"
| Periode | Total Pemasukan | Total Pengeluaran | Saldo Akhir |
|---------|-----------------|-------------------|-------------|
| 2024-12 | 8,500,000 | 2,150,000 | 6,350,000 |

## 🛡️ Security Best Practices

### ⚠️ File Sensitif
JANGAN share file berikut:
- `.env` - API keys dan tokens
- `credentials.json` - OAuth credentials
- `token.json` - Access token Google

### 📝 .gitignore
File `.gitignore` sudah dikonfigurasi untuk mengabaikan file sensitif.

## 🚀 Deployment

### Deploy ke VPS
```bash
# Setup VPS
sudo apt update
sudo apt install python3 python3-pip

# Clone dan setup
git clone [repository]
cd telegram-finance-bot
pip3 install -r requirements.txt

# Setup systemd service
sudo nano /etc/systemd/system/finance-bot.service
```

### Deploy ke Heroku
```bash
# Buat Procfile
echo "worker: python main.py" > Procfile

# Deploy
heroku create finance-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=xxx
heroku config:set GEMINI_API_KEY=xxx
git push heroku main
```

## 📈 Roadmap

- [ ] Export ke PDF
- [ ] Backup otomatis
- [ ] Notifikasi budget
- [ ] Multi-currency support
- [ ] Web dashboard
- [ ] Mobile app

## 🤝 Contributing

Contributions welcome! Silakan:
1. Fork repository
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Buat Pull Request

## 📄 License

MIT License - Open source dan gratis digunakan

## 👨‍💻 Author

Created with ❤️ untuk membantu mengelola keuangan pribadi

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Google Sheets API](https://developers.google.com/sheets)
- [Google Gemini AI](https://ai.google.dev/)
- Community contributors

## 📞 Support

Jika ada pertanyaan atau masalah:
- 📚 Check dokumentasi
- 🔍 Lihat troubleshooting
- 🐛 Buat issue di repository
- 💬 Diskusi di Telegram group

---

**Happy Budgeting! 💰📊**