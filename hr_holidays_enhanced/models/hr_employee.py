# coding: utf-8
from datetime import datetime
from openerp import api, fields, models


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    @api.depends(
        'holidays_ids', 'holidays_ids.date_to', 'holidays_ids.date_from', 'holidays_ids.state',
        'holidays_ids.type', 'holidays_ids.allocation_id', 'holidays_ids.number_of_days_temp',
    )
    def _get_remaining_days(self):
        today = datetime.today().strftime('%Y-%m-%d')
        for employee in self:
            remaining_days = 0.0
            for allocation in employee.holidays_ids.filtered(
                lambda r: (
                    r.date_from <= today and r.date_to >= today and r.type == 'add'
                    and not r.holiday_status_id.limit
                )
            ):
                remaining_days += allocation.number_of_days_temp
                for holiday in allocation.holidays_ids:
                    remaining_days -= holiday.number_of_days_temp
            employee.remaining_leaves = remaining_days

    remaining_leaves = fields.Float(
        compute="_get_remaining_days", string='Remaining Legal Leaves', store=True,
        help='Total number of legal leaves allocated to this employee for the current year',
    )
    holidays_ids = fields.One2many(
        'hr.holidays', 'employee_id', string="Leaves"
    )
