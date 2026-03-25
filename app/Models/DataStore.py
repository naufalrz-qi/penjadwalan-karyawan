from app.Models.Database import db, Branch, Jobdesk, Employee, Setting, SchedulePeriod, DailyShift

def init_data():
    pass

def load_settings():
    s = {}
    pagi = db.session.get(Setting, 'shift_pagi')
    if pagi: s['shift_pagi'] = pagi.value
        
    siang = db.session.get(Setting, 'shift_siang')
    if siang: s['shift_siang'] = siang.value
        
    branches = Branch.query.all()
    b_list = []
    for b in branches:
        jds = [j.name for j in b.jobdesks]
        b_list.append({'id': b.id, 'name': b.name, 'jobdesks': jds})
        
    s['branches'] = b_list
    return s

def save_settings(d):
    if 'shift_pagi' in d:
        pagi = db.session.get(Setting, 'shift_pagi')
        if not pagi:
            pagi = Setting(key='shift_pagi')
            db.session.add(pagi)
        pagi.value = d['shift_pagi']
        
    if 'shift_siang' in d:
        siang = db.session.get(Setting, 'shift_siang')
        if not siang:
            siang = Setting(key='shift_siang')
            db.session.add(siang)
        siang.value = d['shift_siang']
        
    if 'branches' in d:
        new_bids = [b['id'] for b in d['branches']]
        Branch.query.filter(Branch.id.notin_(new_bids)).delete(synchronize_session=False)
        
        for b_data in d['branches']:
            b = db.session.get(Branch, b_data['id'])
            if not b:
                b = Branch(id=b_data['id'])
                db.session.add(b)
            b.name = b_data['name']
            
            Jobdesk.query.filter_by(branch_id=b.id).delete()
            for jd in b_data.get('jobdesks', []):
                db.session.add(Jobdesk(branch_id=b.id, name=jd))
                
    db.session.commit()

def load_employees():
    emps = Employee.query.all()
    return [{'id': e.id, 'name': e.name, 'gender': e.gender, 'branch': e.branch_id, 'jobdesk': e.jobdesk_name} for e in emps]

def save_employees(emps_list):
    new_ids = [e['id'] for e in emps_list]
    Employee.query.filter(Employee.id.notin_(new_ids)).delete(synchronize_session=False)
    
    for e_data in emps_list:
        e = db.session.get(Employee, e_data['id'])
        if not e:
            e = Employee(id=e_data['id'])
            db.session.add(e)
        e.name = e_data['name']
        e.gender = e_data['gender']
        e.branch_id = e_data['branch']
        e.jobdesk_name = e_data['jobdesk']
        
    db.session.commit()

def load_schedule(pk):
    period = db.session.get(SchedulePeriod, pk)
    if not period: return None
    
    p = {
        'period_key': period.period_key,
        'year': period.year,
        'month': period.month,
        'branch_id': period.branch_id,
        'label': period.label,
        'generated': period.generated,
        'dates': [],
    }
    from scheduler import get_period_dates
    p['dates'] = get_period_dates(p['year'], p['month'])
    
    shifts = DailyShift.query.filter_by(period_key=pk).all()
    
    p['schedule'] = {}
    p['off_days'] = {}
    p['cuti_days'] = {}
    
    for s in shifts:
        if s.employee_id not in p['schedule']:
            p['schedule'][s.employee_id] = {}
        p['schedule'][s.employee_id][s.date] = s.status
        
        if s.status == 'OFF':
            p['off_days'].setdefault(s.employee_id, []).append(s.date)
        elif s.status == 'CUTI':
            p['cuti_days'].setdefault(s.employee_id, []).append(s.date)
            
    return p

def save_schedule(pk, data):
    period = db.session.get(SchedulePeriod, pk)
    if not period:
        period = SchedulePeriod(
            period_key=pk, year=data['year'], month=data['month'],
            branch_id=data.get('branch_id'), label=data['label']
        )
        db.session.add(period)
        
    period.generated = data.get('generated', False)
    
    DailyShift.query.filter_by(period_key=pk).delete()
    
    for eid, days in data.get('schedule', {}).items():
        for d, st in days.items():
            db.session.add(DailyShift(
                period_key=pk, employee_id=eid, date=d, status=st
            ))
            
    db.session.commit()

def list_schedules():
    periods = SchedulePeriod.query.order_by(SchedulePeriod.year.desc(), SchedulePeriod.month.desc()).all()
    return [p.period_key for p in periods]

def load_employees_for_period(period):
    emps = load_employees()
    if period and period.get('branch_id'):
        return [e for e in emps if e['branch'] == period['branch_id']]
    return emps

def branch_map(settings):
    return {b['id']: b for b in settings.get('branches', [])}

def group_by_branch(emps, settings):
    bmap   = branch_map(settings)
    result = {}
    for b in settings.get('branches', []):
        result[b['id']] = {'branch': b, 'by_jobdesk': {}}
    for emp in emps:
        bid = emp.get('branch', '')
        jd  = emp['jobdesk']
        if bid not in result:
            result[bid] = {'branch': {'id': bid, 'name': 'Lainnya', 'jobdesks': []}, 'by_jobdesk': {}}
        result[bid]['by_jobdesk'].setdefault(jd, []).append(emp)
    return result

def get_branch(settings, bid):
    for b in settings.get('branches', []):
        if b['id'] == bid:
            return b
    return None

def all_jobdesks(settings):
    seen, out = set(), []
    for b in settings.get('branches', []):
        for jd in b.get('jobdesks', []):
            if jd not in seen:
                seen.add(jd)
                out.append(jd)
    return out

def delete_schedule(pk):
    period = db.session.get(SchedulePeriod, pk)
    if period:
        db.session.delete(period)
        db.session.commit()

