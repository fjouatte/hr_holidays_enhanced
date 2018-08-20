# coding: utf-8
from datetime import datetime, timedelta
import math
from openerp import api, fields, models, tools
from openerp.exceptions import Warning
from openerp.osv import osv
from openerp.tools.translate import _


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
        'hr.holidays', u"Allocation liée", domain=[],
    )
    holidays_ids = fields.One2many(
        'hr.holidays', 'allocation_id', u"Congé(s) lié(s)", domain=[('type', '=', 'remove')]
    )
    is_current_allocation = fields.Boolean(
        compute='_is_current_allocation', string=u"Allocation courante ?",
        search='_search_current_allocation',
    )

    def _get_number_of_days(self, date_from, date_to):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
        daygenerator = (from_dt + timedelta(x + 1) for x in xrange((to_dt - from_dt).days))
        return sum(1 for day in daygenerator if day.weekday() < 5)

    @api.onchange('date_from')
    def onchange_date_from(self):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        date_from, date_to = self.date_from, self.date_to
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(
                _('Warning!'), _('The start date must be anterior to the end date.')
            )

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.strptime(
                date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT
            ) + timedelta(hours=8)
            self.date_to = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            self.number_of_days_temp = round(math.floor(diff_day))+1
        else:
            self.number_of_days_temp = 0

    @api.onchange('date_to')
    def onchange_date_to(self):
        """
        Update the number_of_days.
        """
        date_from, date_to = self.date_from, self.date_to
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(
                _('Warning!'), _('The start date must be anterior to the end date.')
            )

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            self.number_of_days_temp = round(math.floor(diff_day))+1
        else:
            self.number_of_days_temp = 0

    @api.multi
    def get_remaining_days(self):
        remaining_days = self.allocation_id.number_of_days_temp
        for holiday in self.allocation_id.holidays_ids:
            remaining_days -= holiday.number_of_days_temp
        return remaining_days

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

    @api.multi
    def _check_date(self):
        """ on vérifie que la date de congé n'est pas déjà utilisée pour le même employé
        """
        for holiday in self:
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
            nholidays = holiday.search_count(domain)
            if nholidays:
                return False
        return True

    @api.multi
    def _check_availability(self):
        """ on vérifie qu'il existe bien une allocation de congés pour la période demandée
            et qu'il reste des jours à consommer
        """
        for holiday in self:
            if holiday.type == 'add':
                continue
            allocation_id = self.search(
                [
                    ('date_from', '<=', holiday.date_from),
                    ('date_to', '>=', holiday.date_to),
                    ('type', '=', 'add'),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                ], limit=1
            )
            if not allocation_id:
                return False
            """
            remaining_days = allocation_id.number_of_days_temp
            for day in allocation_id.holidays_ids:
                remaining_days -= day.number_of_days_temp
                if remaining_days - holiday.number_of_days_temp < 0:
                    return False
            """
        return True

    @api.multi
    def _check_holidays(self):
        """ on vérifie qu'on ne dépasse pas le nombre de jours disponible """
        for record in self:
            if (
                record.holiday_type != 'employee' or record.type != 'remove' or
                not record.employee_id or record.holiday_status_id.limit
            ):
                continue
            remaining_days = record.get_remaining_days()
            if (remaining_days - record.number_of_days_temp) < 0:
                # Raising a warning gives a more user-friendly feedback than
                # the default constraint error
                raise Warning(
                    _(
                        'The number of remaining leaves is not sufficient for this leave type.\n'
                        'Please verify also the leaves waiting for validation.'
                    )
                )
        return True

    _constraints = [
        (
            _check_date, 'You can not have 2 leaves that overlaps on same day!',
            ['date_from', 'date_to']
        ),
        (_check_availability, 'You can not have leaves for these dates', ['date_from', 'date_to']),
        (
            _check_holidays,
            'The number of remaining leaves is not sufficient for this leave type',
            ['state', 'number_of_days_temp']
        ),
    ]
