from flask import render_template, request, redirect, url_for, jsonify
import uuid
from app.Models.DataStore import load_settings, save_settings, get_branch


class SettingController:

    # ── SSR page (just renders the shell; data loaded via JS) ─────────────────
    @staticmethod
    def index():
        if request.method == 'POST':
            # Legacy form fallback (keep for compatibility)
            s = load_settings()
            s['shift_pagi']  = {'start': request.form['pagi_start'], 'end': request.form['pagi_end']}
            s['shift_siang'] = {'start': request.form['siang_start'], 'end': request.form['siang_end']}
            save_settings(s)
            return redirect(url_for('settings'))
        return render_template('settings.html')

    # ── JSON API ───────────────────────────────────────────────────────────────

    @staticmethod
    def api_get():
        """GET /api/settings → full settings dict as JSON."""
        return jsonify(load_settings())

    @staticmethod
    def api_update_shift():
        """PUT /api/settings/shift → update shift hours."""
        data = request.get_json(force=True) or {}
        s = load_settings()
        s['shift_pagi']  = {'start': data.get('pagi_start', '08:00'), 'end': data.get('pagi_end', '15:00')}
        s['shift_siang'] = {'start': data.get('siang_start', '14:00'), 'end': data.get('siang_end', '21:00')}
        save_settings(s)
        return jsonify({'success': True})

    @staticmethod
    def api_add_branch():
        """POST /api/settings/branch → add branch."""
        data = request.get_json(force=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Nama cabang diperlukan'}), 400
        s = load_settings()
        new_branch = {'id': str(uuid.uuid4()), 'name': name, 'jobdesks': []}
        s.setdefault('branches', []).append(new_branch)
        save_settings(s)
        return jsonify({'success': True, 'branch': new_branch})

    @staticmethod
    def api_update_branch(bid):
        """PUT /api/settings/branch/<bid> → update branch name and/or jobdesks."""
        data = request.get_json(force=True) or {}
        s = load_settings()
        b = get_branch(s, bid)
        if not b:
            return jsonify({'success': False, 'error': 'Cabang tidak ditemukan'}), 404
        if 'name' in data:
            b['name'] = data['name'].strip()
        if 'jobdesks' in data:
            b['jobdesks'] = [j.strip() for j in data['jobdesks'] if j.strip()]
        save_settings(s)
        return jsonify({'success': True, 'branch': b})

    @staticmethod
    def api_delete_branch(bid):
        """DELETE /api/settings/branch/<bid> → delete branch."""
        s = load_settings()
        before = len(s.get('branches', []))
        s['branches'] = [b for b in s.get('branches', []) if b['id'] != bid]
        if len(s['branches']) == before:
            return jsonify({'success': False, 'error': 'Cabang tidak ditemukan'}), 404
        save_settings(s)
        return jsonify({'success': True})

    # ── Legacy form routes (still used as HTML fallback) ──────────────────────
    @staticmethod
    def store_branch():
        s = load_settings()
        s.setdefault('branches', []).append({
            'id': str(uuid.uuid4()), 'name': request.form['name'].strip(), 'jobdesks': []})
        save_settings(s)
        return redirect(url_for('settings'))

    @staticmethod
    def update_branch(bid):
        s = load_settings()
        b = get_branch(s, bid)
        if b:
            b['name'] = request.form.get('name', b['name']).strip()
            raw_textarea = request.form.get('jobdesks', '').strip()
            if raw_textarea:
                b['jobdesks'] = [j.strip() for j in raw_textarea.split('\n') if j.strip()]
            else:
                b['jobdesks'] = [j.strip() for j in request.form.getlist('jobdesks_list[]') if j.strip()]
            save_settings(s)
        return redirect(url_for('settings'))

    @staticmethod
    def destroy_branch(bid):
        s = load_settings()
        s['branches'] = [b for b in s.get('branches', []) if b['id'] != bid]
        save_settings(s)
        return redirect(url_for('settings'))

    @staticmethod
    def api_branch_jobdesks(bid):
        s = load_settings()
        b = get_branch(s, bid)
        return jsonify({'jobdesks': b['jobdesks'] if b else []})
