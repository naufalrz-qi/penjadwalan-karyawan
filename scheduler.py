"""
Aturan penjadwalan (Revisi V2):
  1. Pola Shift: Minimal 1-3 pergantian shift di antara hari OFF (dinamis tergantung panjang blok).
  2. Hierarki Pengelompokan: Jobdesk > Gender (min 2 balance) > Pegawai.
  3. After-OFF Rule: Shift pertama setelah OFF harus berbeda dari shift terakhir sebelum OFF.
  4. Ketetapan OFF: Ditentukan oleh user.
  5. Proporsi Ganjil/Genap:
     - Headcount Ganjil -> Siang lebih banyak.
     - Headcount Genap -> 50:50.
  6. General Base fallback: Jika jobdesk hanya 1-2 orang beda gender, ikut proporsi kategori jobdesk-nya.
"""

import random
from datetime import date, timedelta
import time # Import time for seeding

OPPOSITE = {'PAGI': 'SIANG', 'SIANG': 'PAGI'}


# ─── Public helpers ───────────────────────────────────────────────────────────

def get_period_dates(year, month):
    """Kembalikan list tanggal ISO dari tgl 26 bulan lalu s/d 25 bulan ini."""
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    start = date(prev_year, prev_month, 26)
    end   = date(year, month, 25)
    dates, cur = [], start
    while cur <= end:
        dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return dates


def calculate_summary(period_data, employees):
    """Hitung total PAGI/SIANG/OFF/CUTI per pegawai."""
    schedule = period_data.get('schedule', {})
    summary  = {}
    for emp in employees:
        eid    = emp['id']
        counts = {'PAGI': 0, 'SIANG': 0, 'OFF': 0, 'CUTI': 0}
        for status in schedule.get(eid, {}).values():
            if status in counts:
                counts[status] += 1
        summary[eid] = counts
    return summary


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _last_shift(schedule, eid, all_dates, up_to_idx):
    """Cari PAGI/SIANG terakhir sebelum indeks up_to_idx."""
    for i in range(up_to_idx - 1, -1, -1):
        st = schedule[eid].get(all_dates[i])
        if st in ('PAGI', 'SIANG'):
            return st
    return None


def _get_target_proportions(count):
    """Aturan 5: Ganjil (Siang > Pagi), Genap (50:50)."""
    if count == 0: return 0, 0
    if count % 2 != 0:
        pagi = count // 2
        siang = count - pagi
    else:
        pagi = siang = count // 2
    return pagi, siang


def _group_employees_new(employees):
    """Aturan 2 & 6: Jobdesk > Gender balance fallback."""
    by_jd = {}
    for emp in employees:
        by_jd.setdefault(emp['jobdesk'], []).append(emp)

    groups, general_base = [], []

    for jd, emps in by_jd.items():
        if len(emps) == 1:
            general_base.extend(emps)
            continue
        if len(emps) == 2 and len({e['gender'] for e in emps}) == 2:
            general_base.extend(emps)
            continue

        males = [e for e in emps if e['gender'] == 'P']
        females = [e for e in emps if e['gender'] == 'W']

        if len(males) >= 2 and len(females) >= 2:
            groups.append({'type': 'gender', 'label': f"{jd}-M", 'emps': males, 'jd': jd})
            groups.append({'type': 'gender', 'label': f"{jd}-F", 'emps': females, 'jd': jd})
        else:
            groups.append({'type': 'jobdesk', 'label': jd, 'emps': emps, 'jd': jd})
    
    return groups, general_base


def _generate_block_pattern(length, start_shift, rng):
    """Aturan 1: 1-3 pergantian shift dinamis sesuai panjang blok."""
    if length <= 0: return []
    if length <= 2: num_transitions = 0
    elif length <= 4: num_transitions = 1
    elif length <= 6: num_transitions = rng.randint(1, 2)
    else: num_transitions = rng.randint(2, 3)
    
    current_shift = start_shift if start_shift else rng.choice(['PAGI', 'SIANG'])
    pattern = []
    if num_transitions == 0:
        return [current_shift] * length
    
    points = sorted(rng.sample(range(1, length), num_transitions))
    for i in range(length):
        if i in points: current_shift = OPPOSITE[current_shift]
        pattern.append(current_shift)
    return pattern


# ─── Core scheduler ──────────────────────────────────────────────────────────

def generate_schedule(period_data, employees):
    """Main Scheduler V2."""
    random.seed(time.time())
    all_dates = period_data['dates']
    pk = period_data.get('period_key', 'gen')
    
    off_map   = {k: set(v) for k, v in period_data.get('off_days',  {}).items()}
    cuti_map  = {k: set(v) for k, v in period_data.get('cuti_days', {}).items()}
    fixed = {e['id']: {d: ('OFF' if d in off_map.get(e['id'], set()) else 
                           'CUTI' if d in cuti_map.get(e['id'], set()) else None) 
                       for d in all_dates} for e in employees}

    schedule = {e['id']: {} for e in employees}
    for eid in schedule:
        for d in all_dates:
            if fixed[eid][d]: schedule[eid][d] = fixed[eid][d]
            elif eid in period_data.get('schedule', {}) and d in period_data['schedule'][eid]:
                val = period_data['schedule'][eid][d]
                if val in ('PAGI', 'SIANG'): schedule[eid][d] = val

    groups, general_base = _group_employees_new(employees)

    # Fill Blocks
    all_target_groups = groups + ([{'emps': [e for e in general_base if e['jobdesk'] == jd], 'jd': jd} 
                                  for jd in {e['jobdesk'] for e in general_base}] if general_base else [])

    for group in all_target_groups:
        for emp in group['emps']:
            eid, in_block = emp['id'], []
            rng = random.Random(f"{eid}-{pk}")
            for i, d in enumerate(all_dates):
                if fixed[eid][d] is None: in_block.append(i)
                if (fixed[eid][d] or i == len(all_dates)-1) and in_block:
                    ls = _last_shift(schedule, eid, all_dates, in_block[0])
                    start_sh = OPPOSITE[ls] if ls else rng.choice(['PAGI', 'SIANG'])
                    pattern = _generate_block_pattern(len(in_block), start_sh, rng)
                    for idx, day_idx in enumerate(in_block):
                        if schedule[eid].get(all_dates[day_idx]) not in ('PAGI', 'SIANG', 'OFF', 'CUTI'):
                            schedule[eid][all_dates[day_idx]] = pattern[idx]
                    in_block = []

    # 6. Balancing Harian (Aggressive Proportion Fix per Jobdesk)
    # Kita kumpulkan semua pegawai per Jobdesk agar balancing lebih fleksibel
    all_jds = {e['jobdesk'] for e in employees}
    for jd in all_jds:
        jd_emps = [e for e in employees if e['jobdesk'] == jd]
        target_p, _ = _get_target_proportions(len(jd_emps))
        ratio_p = target_p / len(jd_emps) if len(jd_emps) > 0 else 0.5
        
        for d_idx, d in enumerate(all_dates):
            working = [e for e in jd_emps if fixed[e['id']][d] is None]
            if not working: continue
            
            day_target_p = int(len(working) * ratio_p)
            
            flexible_ids = []
            locked_ids = []
            for e in working:
                eid = e['id']
                if d_idx > 0 and fixed[eid][all_dates[d_idx-1]] is not None:
                    locked_ids.append(eid)
                else:
                    flexible_ids.append(eid)
            
            pagi_now = [eid for eid in [e['id'] for e in working] if schedule[eid].get(d) == 'PAGI']
            siang_now = [eid for eid in [e['id'] for e in working] if schedule[eid].get(d) == 'SIANG']
            
            # Jika kelebihan PAGI
            if len(pagi_now) > day_target_p:
                excess = len(pagi_now) - day_target_p
                flex_pagi = [eid for eid in flexible_ids if eid in pagi_now]
                random.shuffle(flex_pagi)
                for eid in flex_pagi[:excess]:
                    schedule[eid][d] = 'SIANG'
            # Jika kekurangan PAGI
            elif len(pagi_now) < day_target_p:
                needed = day_target_p - len(pagi_now)
                flex_siang = [eid for eid in flexible_ids if eid in siang_now]
                random.shuffle(flex_siang)
                for eid in flex_siang[:needed]:
                    schedule[eid][d] = 'PAGI'

    return schedule