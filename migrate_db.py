import os
import json
from run import app
from app.Models.Database import db, Branch, Jobdesk, Employee, Setting, SchedulePeriod, DailyShift

DATA_DIR = 'data'
EMPLOYEES_FILE = os.path.join(DATA_DIR, 'employees.json')
SETTINGS_FILE  = os.path.join(DATA_DIR, 'settings.json')
SCHEDULES_DIR  = os.path.join(DATA_DIR, 'schedules')

def run_migration():
    with app.app_context():
        # Pastikan tabel dibuat
        db.create_all()

        print("Memulai Ekstraksi Migrasi dari JSON ke SQLite...")

        # 1. Pindah Pengaturan (Settings & Branch)
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            if 'shift_pagi' in settings:
                if not db.session.get(Setting, 'shift_pagi'):
                    db.session.add(Setting(key='shift_pagi', value=settings['shift_pagi']))
            
            if 'shift_siang' in settings:
                if not db.session.get(Setting, 'shift_siang'):
                    db.session.add(Setting(key='shift_siang', value=settings['shift_siang']))
            
            for b in settings.get('branches', []):
                branch = db.session.get(Branch, b['id'])
                if not branch:
                    branch = Branch(id=b['id'], name=b['name'])
                    db.session.add(branch)
                
                # Extract array of string jobdesks into Jobdesk Relational Table
                for jd_name in b.get('jobdesks', []):
                    existing_jd = Jobdesk.query.filter_by(branch_id=b['id'], name=jd_name).first()
                    if not existing_jd:
                        db.session.add(Jobdesk(branch_id=b['id'], name=jd_name))
        
        # 2. Pindah Pegawai
        if os.path.exists(EMPLOYEES_FILE):
            with open(EMPLOYEES_FILE, 'r', encoding='utf-8') as f:
                employees = json.load(f)
            
            for emp in employees:
                if not db.session.get(Employee, emp['id']):
                    db.session.add(Employee(
                        id=emp['id'],
                        name=emp['name'],
                        gender=emp['gender'],
                        branch_id=emp['branch'],
                        jobdesk_name=emp['jobdesk']
                    ))

        # Commit Tahap 1 untuk menyegel Foreign Key Parent
        db.session.commit()
        print("[OK] Sukses mengimpor Branch, Setting, dan Employee")
        
        # 3. Pindah Data Jadwal Induk & Shifting Harian
        if os.path.exists(SCHEDULES_DIR):
            for filename in os.listdir(SCHEDULES_DIR):
                if not filename.endswith('.json'):
                    continue
                filepath = os.path.join(SCHEDULES_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    sched_data = json.load(f)
                
                pk = sched_data['period_key']
                period = db.session.get(SchedulePeriod, pk)
                if not period:
                    period = SchedulePeriod(
                        period_key=pk,
                        year=sched_data['year'],
                        month=sched_data['month'],
                        branch_id=sched_data.get('branch_id', '') or None,
                        label=sched_data['label'],
                        generated=sched_data.get('generated', False)
                    )
                    db.session.add(period)
                
                # Mengurai JSON shift calendar ke Entity log terpisah
                schedule_dict = sched_data.get('schedule', {})
                for eid, days in schedule_dict.items():
                    for day_date, status in days.items():
                        existing_shift = DailyShift.query.filter_by(
                            period_key=pk, employee_id=eid, date=day_date
                        ).first()
                        if not existing_shift:
                            db.session.add(DailyShift(
                                period_key=pk,
                                employee_id=eid,
                                date=day_date,
                                status=status
                            ))
        
        db.session.commit()
        print("[OK] Sukses mengekstrak Schedule Calendar")
        print("Migrasi Database Anda Selesai! (Semua data JSON sudah tersedot ke SQLite!)")

if __name__ == '__main__':
    run_migration()
 