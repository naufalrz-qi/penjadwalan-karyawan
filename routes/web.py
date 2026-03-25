from app.Http.Controllers.HomeController import HomeController
from app.Http.Controllers.EmployeeController import EmployeeController
from app.Http.Controllers.SettingController import SettingController
from app.Http.Controllers.ScheduleController import ScheduleController

def register_web_routes(app):
    # --- Home ---
    app.add_url_rule('/', endpoint='index', view_func=HomeController.index, methods=['GET'])

    # --- Employees ---
    app.add_url_rule('/employees', endpoint='employees', view_func=EmployeeController.index, methods=['GET'])
    app.add_url_rule('/employees/add', endpoint='add_employee', view_func=EmployeeController.store, methods=['POST'])
    app.add_url_rule('/employees/inline/<eid>', endpoint='inline_edit_employee', view_func=EmployeeController.inline_update, methods=['POST'])
    app.add_url_rule('/employees/edit/<eid>', endpoint='edit_employee', view_func=EmployeeController.update, methods=['POST'])
    app.add_url_rule('/employees/delete/<eid>', endpoint='delete_employee', view_func=EmployeeController.destroy, methods=['POST'])

    # --- Settings ---
    app.add_url_rule('/settings', endpoint='settings', view_func=SettingController.index, methods=['GET', 'POST'])
    app.add_url_rule('/settings/branch/add', endpoint='add_branch', view_func=SettingController.store_branch, methods=['POST'])
    app.add_url_rule('/settings/branch/<bid>/edit', endpoint='edit_branch', view_func=SettingController.update_branch, methods=['POST'])
    app.add_url_rule('/settings/branch/<bid>/delete', endpoint='delete_branch', view_func=SettingController.destroy_branch, methods=['POST'])
    app.add_url_rule('/api/branch/<bid>/jobdesks', endpoint='api_branch_jobdesks', view_func=SettingController.api_branch_jobdesks, methods=['GET'])
    # JSON API
    app.add_url_rule('/api/settings', endpoint='api_settings_get', view_func=SettingController.api_get, methods=['GET'])
    app.add_url_rule('/api/settings/shift', endpoint='api_settings_shift', view_func=SettingController.api_update_shift, methods=['PUT'])
    app.add_url_rule('/api/settings/branch', endpoint='api_add_branch_json', view_func=SettingController.api_add_branch, methods=['POST'])
    app.add_url_rule('/api/settings/branch/<bid>', endpoint='api_update_branch', view_func=SettingController.api_update_branch, methods=['PUT'])
    app.add_url_rule('/api/settings/branch/<bid>', endpoint='api_delete_branch', view_func=SettingController.api_delete_branch, methods=['DELETE'])

    # --- Schedule ---
    app.add_url_rule('/schedule/new', endpoint='new_schedule', view_func=ScheduleController.store, methods=['POST'])
    app.add_url_rule('/schedule/<pk>/setup', endpoint='schedule_setup', view_func=ScheduleController.setup, methods=['GET'])
    app.add_url_rule('/schedule/<pk>/save_off', endpoint='save_off', view_func=ScheduleController.save_off, methods=['POST'])
    app.add_url_rule('/schedule/<pk>/auto_off_template', endpoint='auto_off_template', view_func=ScheduleController.auto_off_template, methods=['POST'])
    app.add_url_rule('/schedule/<pk>/generate', endpoint='generate', view_func=ScheduleController.generate, methods=['POST'])
    app.add_url_rule('/schedule/<pk>', endpoint='schedule_view', view_func=ScheduleController.show, methods=['GET'])
    app.add_url_rule('/schedule/<pk>/edit_cell', endpoint='edit_cell', view_func=ScheduleController.edit_cell, methods=['POST'])
    app.add_url_rule('/schedule/<pk>/delete', endpoint='delete_schedule', view_func=ScheduleController.destroy, methods=['POST'])
    app.add_url_rule('/schedule/<pk>/export/excel', endpoint='export_excel', view_func=ScheduleController.export_excel, methods=['GET'])
    app.add_url_rule('/schedule/<pk>/export/pdf', endpoint='export_pdf', view_func=ScheduleController.export_pdf, methods=['GET'])
