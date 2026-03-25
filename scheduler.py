"""
Aturan penjadwalan:
  1. Consecutive shifts  : setiap pegawai mendapat shift yang SAMA 2–4 hari berturut-turut,
                           baru kemudian berganti shift (kecuali ada OFF/CUTI).
  2. Daily balance       : #PAGI = 40%, #SIANG = 60% per (cabang, jobdesk) per hari.
  3. Personal balance    : total PAGI ~ 40% total jadwal kerja pegawai sepanjang periode.
  4. After-OFF/CUTI rule : shift pertama setelah blok OFF/CUTI HARUS BERBEDA
                           dari shift terakhir sebelum blok OFF/CUTI.
  5. Gender balance      : Proporsi 40:60 (Pagi:Siang) dipastikan secara
                           independen untuk Laki-laki (P) dan Perempuan (W).
"""

import random
from datetime import date, timedelta

OPPOSITE = {'PAGI': 'SIANG', 'SIANG': 'PAGI'}


# ─── Public helpers ───────────────────────────────────────────────────────────

def get_period_dates(year, month):
    """Kembalikan list tanggal ISO dari tgl 26 bulan lalu s/d 25 bulan ini.
    Contoh: April → 26 Maret s/d 25 April (selalu 31 hari).
    """
    # Bulan sebelumnya
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


# ─── Core scheduler ──────────────────────────────────────────────────────────

def generate_schedule(period_data, employees):
    """
    Buat jadwal shift dengan:
      - Blok 2–4 hari berturut-turut (consecutive) per pegawai.
      - Staggering fase awal antar pegawai agar tidak semua ganti shift bareng.
      - Daily 40% PAGI dan 60% SIANG per (cabang, jobdesk) dipastikan per gender.
      - After-OFF/CUTI: otomatis flip shift.
    """
    all_dates = period_data['dates']
    off_map   = {k: set(v) for k, v in period_data.get('off_days',  {}).items()}
    cuti_map  = {k: set(v) for k, v in period_data.get('cuti_days', {}).items()}

    # fixed[eid][date] = 'OFF' | 'CUTI' | None (hari kerja)
    fixed = {}
    for emp in employees:
        eid = emp['id']
        fixed[eid] = {
            d: ('OFF'  if d in off_map.get(eid,  set()) else
                'CUTI' if d in cuti_map.get(eid, set()) else None)
            for d in all_dates
        }

    schedule = {emp['id']: {} for emp in employees}

    # Tulis status tetap (OFF/CUTI) langsung
    for emp in employees:
        eid = emp['id']
        for d in all_dates:
            if fixed[eid][d] is not None:
                schedule[eid][d] = fixed[eid][d]

    # Kelompokkan per (cabang, jobdesk)
    by_bjd = {}
    for emp in employees:
        key = (emp.get('branch', ''), emp['jobdesk'])
        by_bjd.setdefault(key, []).append(emp)

    # Total hari kerja per pegawai (untuk personal balance)
    total_work = {
        emp['id']: sum(1 for d in all_dates if fixed[emp['id']][d] is None)
        for emp in employees
    }
    emp_pagi  = {emp['id']: 0 for emp in employees}
    emp_siang = {emp['id']: 0 for emp in employees}

    # ── Inisialisasi state streak per pegawai ─────────────────────────────────
    #
    # State: shift (shift aktif), remaining (sisa hari paksa di shift ini), rng
    #
    # Staggering:
    #   Pegawai diproses terpisah per gender. Diset 40% awal PAGI (idx mod 5 < 2).
    #   Phase_used (0-3) = seolah-olah sudah menggunakan beberapa hari dari blok pertama,
    #   sehingga antar pegawai tidak ganti shift pada hari yang sama.
    #
    emp_state = {}
    for (branch, jd), emps in by_bjd.items():
        males   = [e for e in emps if e['gender'] == 'P']
        females = [e for e in emps if e['gender'] == 'W']

        def _init_group(group):
            target = round(len(group) * 0.4)
            for idx, emp in enumerate(group):
                eid         = emp['id']
                rng         = random.Random(eid)
                start_shift = 'PAGI' if idx < target else 'SIANG'
                phase_used  = idx % 4
                block_len   = rng.randint(2, 4)
                remaining   = max(0, block_len - phase_used)
                emp_state[eid] = {
                    'shift':     start_shift,
                    'remaining': remaining,
                    'rng':       rng,
                }
        
        _init_group(males)
        _init_group(females)

    # ── Penugasan hari per hari ───────────────────────────────────────────────
    for d_idx, d in enumerate(all_dates):
        for (branch, jd), emps in by_bjd.items():
            working = [e for e in emps if fixed[e['id']][d] is None]
            if not working:
                continue

            working_m = [e for e in working if e['gender'] == 'P']
            working_w = [e for e in working if e['gender'] == 'W']
            
            target_pagi_m = round(len(working_m) * 0.4)
            target_pagi_w = round(len(working_w) * 0.4)

            # forced : eid → shift (mid-streak ATAU baru balik dari OFF)
            # free_m/w : pegawai yang mulai blok baru hari ini
            forced = {}
            free_m = []
            free_w = []

            for emp in working:
                eid   = emp['id']
                state = emp_state[eid]
                is_m  = emp['gender'] == 'P'

                prev_off = (d_idx > 0 and
                            fixed[eid][all_dates[d_idx - 1]] in ('OFF', 'CUTI'))

                if prev_off:
                    # ─ After-OFF rule ─
                    ls = _last_shift(schedule, eid, all_dates, d_idx)
                    if ls:
                        new_sh = OPPOSITE[ls]
                        # Mulai blok baru dengan 2-4 hari (inklusif hari ini)
                        state.update({
                            'shift':     new_sh,
                            'remaining': state['rng'].randint(2, 4),
                        })
                        forced[eid] = new_sh
                    else:
                        if is_m: free_m.append(emp)
                        else: free_w.append(emp)
                    continue

                if state['remaining'] > 0:
                    forced[eid] = state['shift']   # masih dalam streak
                else:
                    if is_m: free_m.append(emp)
                    else: free_w.append(emp)      # blok habis → mulai baru

            # ── Strict Cap Enforcement ──
            # Cegah PAGI berlebih (karena overlapping streak atau rule After-OFF)
            def enforce_cap(gender_list, target_pagi):
                forced_pagi = [e for e in gender_list if e['id'] in forced and forced[e['id']] == 'PAGI']
                if len(forced_pagi) > target_pagi:
                    # Sort berdasarkan yang sudah dapet paling banyak PAGI di assign ke SIANG
                    forced_pagi.sort(key=lambda e: emp_pagi[e['id']], reverse=True)
                    excess = len(forced_pagi) - target_pagi
                    for e in forced_pagi[:excess]:
                        _eid = e['id']
                        forced[_eid] = 'SIANG'
                        emp_state[_eid]['shift'] = 'SIANG'
                        # Mulai hitungan block SIANG baru yang sedikit lebih pendek
                        emp_state[_eid]['remaining'] = max(1, emp_state[_eid]['rng'].randint(2, 4) - 1)
            
            enforce_cap(working_m, target_pagi_m)
            enforce_cap(working_w, target_pagi_w)

            # Tugaskan forced, hitung hari ini per gender
            day_pagi_m = day_pagi_w = 0
            for emp in working:
                eid = emp['id']
                if eid not in forced:
                    continue
                sh    = forced[eid]
                state = emp_state[eid]
                schedule[eid][d]   = sh
                state['remaining'] = max(0, state['remaining'] - 1)
                
                is_m = emp['gender'] == 'P'
                if sh == 'PAGI':
                    emp_pagi[eid]  += 1
                    if is_m: day_pagi_m += 1
                    else: day_pagi_w += 1
                else:
                    emp_siang[eid] += 1

            # Hitung sisa slot PAGI yang dibutuhkan hari ini per gender
            slots_p_m = max(0, min(len(free_m), target_pagi_m - day_pagi_m))
            slots_p_w = max(0, min(len(free_w), target_pagi_w - day_pagi_w))

            # Urutkan berdasarkan defisit PAGI personal 40% (terbesar → dapat PAGI)
            sorted_free_m = sorted(
                free_m,
                key=lambda e: total_work[e['id']] * 0.4 - emp_pagi[e['id']],
                reverse=True,
            )
            sorted_free_w = sorted(
                free_w,
                key=lambda e: total_work[e['id']] * 0.4 - emp_pagi[e['id']],
                reverse=True,
            )

            # Tugaskan free employees Laki-laki
            for i, emp in enumerate(sorted_free_m):
                eid   = emp['id']
                sh    = 'PAGI' if i < slots_p_m else 'SIANG'
                state = emp_state[eid]
                schedule[eid][d]   = sh
                state['shift']     = sh
                state['remaining'] = state['rng'].randint(1, 3)
                if sh == 'PAGI':
                    emp_pagi[eid]  += 1
                else:
                    emp_siang[eid] += 1

            # Tugaskan free employees Perempuan
            for i, emp in enumerate(sorted_free_w):
                eid   = emp['id']
                sh    = 'PAGI' if i < slots_p_w else 'SIANG'
                state = emp_state[eid]
                schedule[eid][d]   = sh
                state['shift']     = sh
                state['remaining'] = state['rng'].randint(1, 3)
                if sh == 'PAGI':
                    emp_pagi[eid]  += 1
                else:
                    emp_siang[eid] += 1

    # ── Safety pass: pastikan after-OFF rule tidak dilanggar ─────────────────
    schedule = _enforce_after_off(schedule, fixed, employees, all_dates)
    return schedule


def _enforce_after_off(schedule, fixed, employees, all_dates):
    """
    Pass terakhir: periksa setiap hari-pertama-kerja setelah OFF/CUTI.
    Jika shift-nya sama dengan shift sebelum OFF, flip — namun tetap
    menghormati kuota harian 40% PAGI per gender per (branch, jobdesk).

    Logika:
    - Hitung jumlah PAGI yang sudah ada di hari d untuk gender yang sama
      dalam kelompok (branch, jobdesk) yang sama.
    - Hitung total working (tidak OFF/CUTI) pada hari d untuk kelompok tsb.
    - target_cap = round(n_working_gender * 0.4)
    - Jika flip → PAGI tapi hari itu sudah mencapai cap, flip ke SIANG saja.
    - Jika flip → SIANG tidak ada batasan, langsung dilakukan.
    """
    # Buat lookup: emp_id → emp dict
    emp_map = {e['id']: e for e in employees}

    # Buat lookup: emp_id → (branch, jobdesk)
    emp_bjd = {
        e['id']: (e.get('branch', ''), e['jobdesk'])
        for e in employees
    }

    # Kelompokkan semua emp per (branch, jobdesk)
    by_bjd = {}
    for e in employees:
        key = (e.get('branch', ''), e['jobdesk'])
        by_bjd.setdefault(key, []).append(e)

    for emp in employees:
        eid   = emp['id']
        bjd   = emp_bjd[eid]
        gender = emp.get('gender', 'P')

        for d_idx in range(1, len(all_dates)):
            d    = all_dates[d_idx]
            prev = all_dates[d_idx - 1]

            if fixed[eid][d] is not None:                    # tetap OFF/CUTI
                continue
            if fixed[eid][prev] not in ('OFF', 'CUTI'):      # bukan setelah OFF
                continue

            cur = schedule[eid].get(d)
            if cur not in ('PAGI', 'SIANG'):
                continue

            ls = _last_shift(schedule, eid, all_dates, d_idx)
            if not ls or cur != ls:
                continue  # tidak perlu flip

            # Perlu flip dari cur ke OPPOSITE[cur]
            want = OPPOSITE[cur]

            if want == 'PAGI':
                # Cek apakah kuota PAGI harian sudah penuh untuk gender ini
                group = by_bjd.get(bjd, [])
                working_gender = [
                    e for e in group
                    if e['gender'] == gender and fixed[e['id']][d] is None
                ]
                cap = round(len(working_gender) * 0.4)
                pagi_now = sum(
                    1 for e in working_gender
                    if schedule.get(e['id'], {}).get(d) == 'PAGI'
                )
                if pagi_now >= cap:
                    # Kuota penuh → tetap SIANG (jangan flip)
                    # Hanya pastikan cur tidak sama dengan ls sesuai aturan;
                    # jika memang harus beda dan PAGI penuh, pakai SIANG.
                    schedule[eid][d] = 'SIANG'
                    continue

            schedule[eid][d] = want

    return schedule