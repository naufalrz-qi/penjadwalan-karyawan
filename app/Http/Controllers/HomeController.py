from flask import render_template
from datetime import date
from sqlalchemy import func
from app.Models.Database import db, Employee, DailyShift
from app.Models.DataStore import load_settings, branch_map, list_schedules, load_schedule

MONTH_NAMES = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

class HomeController:
    @staticmethod
    def index():
        settings  = load_settings()
        bmap      = branch_map(settings)
        schedules = []
        for pk in list_schedules():
            data  = load_schedule(pk)
            if not data:
                continue
            bid   = data.get('branch_id') or ''
            bname = bmap[bid]['name'] if bid and bid in bmap else 'Semua Cabang'
            parts = pk.split('-')
            y, m  = int(parts[0]), int(parts[1])
            schedules.append({
                'key':         pk,
                'label':       f"{MONTH_NAMES[m]} {y}",
                'branch_name': bname,
                'generated':   data.get('generated', False),
            })
            
        # Analytics Data
        total_employees = Employee.query.count()
        
        genders = db.session.query(Employee.gender, func.count(Employee.id)).group_by(Employee.gender).all()
        gender_stats = {'P': 0, 'W': 0}
        for g, c in genders:
            gender_stats[g] = c
            
        shifts = db.session.query(DailyShift.status, func.count(DailyShift.id)).group_by(DailyShift.status).all()
        shift_stats = { 'PAGI': 0, 'SIANG': 0, 'OFF': 0, 'CUTI': 0 }
        for s, c in shifts:
            if s in shift_stats:
                shift_stats[s] = c
                
        stats = {
            'total_employees': total_employees,
            'gender': gender_stats,
            'shifts': shift_stats,
        }
            
        today = date.today()
        return render_template('index.html', schedules=schedules, today=today,
                               month_names=MONTH_NAMES[1:], settings=settings, stats=stats)
