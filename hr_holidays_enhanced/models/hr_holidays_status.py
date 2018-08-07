from openerp import api, models


class HrHolidaysStatus(models.Model):

    _inherit = 'hr.holidays.status'

    @api.multi
    def name_get(self):
        res = []
        context = self.env.context
        if context is None:
            context = {}
        if not context.get('employee_id', False):
            return super(HrHolidaysStatus, self).name_get()
        for record in self:
            res.append((record.id, record.name))
        return res
