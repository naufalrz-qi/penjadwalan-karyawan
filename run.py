"""
ShiftScheduler — Aplikasi Penjadwalan Shift
Jalankan: python run.py
Buka di browser: http://localhost:5000
"""
from app import app, init_data

if __name__ == '__main__':
    init_data()
    print("\n" + "="*50)
    print("  ShiftScheduler berjalan!")
    print("  Buka: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=False, port=5000)
