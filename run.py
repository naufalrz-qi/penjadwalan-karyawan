from flask import Flask
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.web import register_web_routes
from app.Models.Database import db

app = Flask(__name__)

# Konfigurasi Database SQLite
db_path = os.path.join(app.root_path, 'data', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind DB ke aplikasi Flask
db.init_app(app)

# Daftarkan rute ala Laravel
register_web_routes(app)

if __name__ == '__main__':
    # Buat tabel jika belum ada
    with app.app_context():
        db.create_all()

    print("\n" + "="*50)
    print("  ShiftScheduler (SQLite + Laravel Architecture)")
    print("  Buka: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
