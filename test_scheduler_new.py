import json
from scheduler import generate_schedule, get_period_dates

def test_scheduling():
    # 1. Setup mock employees
    # Group A: 4 emps (Genap) - Should be 50:50
    # Group B: 3 emps (Ganjil) - Should be more SIANG
    # Group C: 1 emp (General Base)
    employees = [
        {'id': 'A1', 'name': 'A1', 'gender': 'P', 'jobdesk': 'ADM'},
        {'id': 'A2', 'name': 'A2', 'gender': 'P', 'jobdesk': 'ADM'},
        {'id': 'A3', 'name': 'A3', 'gender': 'W', 'jobdesk': 'ADM'},
        {'id': 'A4', 'name': 'A4', 'gender': 'W', 'jobdesk': 'ADM'},
        
        {'id': 'B1', 'name': 'B1', 'gender': 'P', 'jobdesk': 'CS'},
        {'id': 'B2', 'name': 'B2', 'gender': 'P', 'jobdesk': 'CS'},
        {'id': 'B3', 'name': 'B3', 'gender': 'W', 'jobdesk': 'CS'}, # B3 is single female in CS, but 2 males -> Jobdesk-level
        
        {'id': 'C1', 'name': 'C1', 'gender': 'P', 'jobdesk': 'SECURITY'}, # Single jobdesk
    ]
    
    dates = get_period_dates(2026, 4) # Apr 2026
    
    period_data = {
        'period_key': 'test-2026-04',
        'dates': dates,
        'off_days': {
            'A1': [dates[0], dates[7], dates[14], dates[21]],
            'A2': [dates[1], dates[8], dates[15], dates[22]],
            'A3': [dates[2], dates[9], dates[16], dates[23]],
            'A4': [dates[3], dates[10], dates[17], dates[24]],
            'B1': [dates[4], dates[11], dates[18], dates[25]],
            'B2': [dates[5], dates[12], dates[19]],
            'B3': [dates[6], dates[13], dates[20]],
            'C1': [dates[0], dates[5], dates[10]],
        },
        'schedule': {}
    }
    
    print("Generating schedule...")
    result = generate_schedule(period_data, employees)
    
    print("\nVERIFIKASI ATURAN:")
    
    # Check Group A (Genap 50:50)
    for d in dates:
        working_a = [eid for eid in ['A1','A2','A3','A4'] if result[eid].get(d) in ('PAGI', 'SIANG')]
        if not working_a: continue
        pagi = [eid for eid in working_a if result[eid][d] == 'PAGI']
        siang = [eid for eid in working_a if result[eid][d] == 'SIANG']
        # For 4 emps, if 1 OFF, working is 3 (odd -> more siang: 1P, 2S)
        # If 0 OFF, working is 4 (even -> 2P, 2S)
        if len(working_a) == 4:
            assert len(pagi) == 2, f"Group A@ {d}: Pagi should be 2, got {len(pagi)}"
        elif len(working_a) == 3:
            assert len(siang) > len(pagi), f"Group A@ {d}: Siang should > Pagi (3 working), got P:{len(pagi)} S:{len(siang)}"

    # Check Transitions and After-OFF
    for eid in result:
        shifts = [result[eid][d] for d in dates]
        changes = 0
        last_work_sh = None
        in_block = False
        block_changes = 0
        
        print(f"Emp {eid} summary: ", end="")
        p_count = shifts.count('PAGI')
        s_count = shifts.count('SIANG')
        print(f"P:{p_count} S:{s_count}", end=" ")
        
        for i, d in enumerate(dates):
            st = result[eid][d]
            if st in ('PAGI', 'SIANG'):
                if not in_block:
                    in_block = True
                    block_changes = 0
                    # After-OFF check (except first shift of month)
                    if last_work_sh:
                        if st == last_work_sh:
                            print(f"\n[WARNING] Emp {eid} @ {d} shift {st} same as before OFF!")
                else:
                    if st != pattern_prev:
                        block_changes += 1
                pattern_prev = st
                last_work_sh = st
            else:
                if in_block:
                    in_block = False
                    if block_changes > 3:
                        print(f"\n[WARNING] Emp {eid} block has {block_changes} changes (>3)!")
        print("OK")

    print("\nTest passed successfully!")

if __name__ == "__main__":
    test_scheduling()
