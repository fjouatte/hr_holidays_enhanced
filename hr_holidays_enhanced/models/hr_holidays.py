# coding: utf-8
from datetime import datetime
from openerp import api, fields, models


class HrHolidays(models.Model):

    _inherit = 'hr.holidays'

    date_from = fields.Datetime(
        'Start Date', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        select=True, copy=False, required=True,
    )
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=True,
        states={
            'draft': [('readonly', False)],
            'confirm': [('readonly', False)]
        },
    )
    allocation_id = fields.Many2one(
        'hr.holidays', u"Allocation liée", domain=[('is_current_allocation', '=', True)],
    )
    holidays_ids = fields.One2many(
        'hr.holidays', 'allocation_id', u"Congé(s) lié(s)", domain=[('type', '=', 'remove')]
    )
    is_current_allocation = fields.Boolean(
        compute='_is_current_allocation', string=u"Allocation courante ?",
        search='_search_current_allocation',
    )

    def _search_current_allocation(self, operator, value):
        today = datetime.today().strftime('%Y-%m-%d')
        return [
            '&', '&', ('type', '=', 'add'), ('date_from', '<=', today), ('date_to', '>=', today)
        ]

    @api.depends('date_from', 'date_to')
    def _is_current_allocation(self):
        today = datetime.today().strftime('%Y-%m-%d')
        for record in self:
            if record.type == 'add' and record.date_from <= today and record.date_to >= today:
                record.is_current_allocation = True
                continue
            record.is_current_allocation = False

    def _check_date(self, cr, uid, ids, context=None):
        for holiday in self.browse(cr, uid, ids, context=context):
            if holiday.type == 'add':
                continue
            domain = [
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>=', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('type', '=', holiday.type),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(cr, uid, domain, context=context)
            if nholidays:
                return False
        return True

    def _check_availability(self, cr, uid, ids, context=None):
        """ on vérifie qu'il existe bien une allocation de congés pour la période demandée """
        for holiday in self.browse(cr, uid, ids, context=context):
            if holiday.type == 'add':
                continue
            allocation_ids = self.search(
                cr, uid, [
                    ('date_from', '<=', holiday.date_from),
                    ('date_to', '>=', holiday.date_to),
                    ('type', '=', 'add')
                ]
            )
            if not allocation_ids:
                return False
        return True

    _constraints = [
        (
            _check_date, 'You can not have 2 leaves that overlaps on same day!', [
                'date_from', 'date_to'
            ]
        ),
        (_check_availability, 'You can not have leaves for these dates', ['date_from', 'date_to']),
    ]
