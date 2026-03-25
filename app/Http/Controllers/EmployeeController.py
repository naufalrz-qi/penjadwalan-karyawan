from flask import render_template, request, jsonify, redirect, url_for
import uuid
from app.Models.DataStore import (
    load_employees, save_employees, load_settings, 
    branch_map, group_by_branch, all_jobdesks
)

class EmployeeController:
    @staticmethod
    def index():
        emps     = load_employees()
        settings = load_settings()
        bmap     = branch_map(settings)

        for e in emps:
            bid = e.get('branch', '')
            e['branch_name'] = bmap.get(bid, {}).get('name', 'Tidak diketahui')

        by_branch   = group_by_branch(emps, settings)
        jd_all      = all_jobdesks(settings)

        return render_template(
            'employees.html',
            employees=emps,
            jobdesks=jd_all,
            by_branch=by_branch,
            settings=settings,
        )

    @staticmethod
    def store():
        emps = load_employees()
        new_emp = {
            'id':      str(uuid.uuid4()),
            'name':    request.form['name'].strip(),
            'branch':  request.form.get('branch', ''),
            'jobdesk': request.form['jobdesk'],
            'gender':  request.form['gender'],
        }
        emps.append(new_emp)
        save_employees(emps)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'employee': new_emp})
        return redirect(url_for('employees'))

    @staticmethod
    def inline_update(eid):
        data = request.get_json()
        if not data:
            return jsonify({'success': False})
        
        field = data.get('field')
        value = data.get('value')
        
        emps = load_employees()
        for e in emps:
            if e['id'] == eid:
                if field in ['name', 'jobdesk', 'gender']:
                    e[field] = value
                save_employees(emps)
                return jsonify({'success': True})
                
        return jsonify({'success': False})

    @staticmethod
    def update(eid):
        emps = load_employees()
        for e in emps:
            if e['id'] == eid:
                e['name']    = request.form['name'].strip()
                e['branch']  = request.form.get('branch', e.get('branch', ''))
                e['jobdesk'] = request.form['jobdesk']
                e['gender']  = request.form['gender']
                break
        save_employees(emps)
        return redirect(url_for('employees'))

    @staticmethod
    def destroy(eid):
        emps = [e for e in load_employees() if e['id'] != eid]
        save_employees(emps)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('employees'))
