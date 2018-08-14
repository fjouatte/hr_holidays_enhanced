import anybox.testing.datetime # noqa
from anybox.testing.openerp import SharedSetupTransactionCase
from datetime import datetime
from openerp.exceptions import ValidationError


class TestHrEmployee(SharedSetupTransactionCase):

    _data_files = ('data.xml', )
    _module_ns = 'tests'

    def setUp(self):
        super(TestHrEmployee, self).setUp()
        datetime.set_now(datetime(2018, 8, 8, 0, 0, 0))
        self.fjouatte = self.env.ref('tests.employee_fjouatte')
        self.fjouatte2 = self.env.ref('tests.employee_fjouatte2')
        self.hr_holidays = self.env['hr.holidays']
        self.allocation = self.hr_holidays.create(
            {
                'employee_id': self.fjouatte.id,
                'holiday_status_id': self.ref('tests.holiday_status_cp'),
                'type': 'add',
                'date_from': '2018-06-01 00:00:01',
                'date_to': '2019-05-31 23:59:59',
                'number_of_days_temp': 25,
            }
        )
        self.leave = self.hr_holidays.create(
            {
                'employee_id': self.fjouatte.id,
                'holiday_status_id': self.ref('tests.holiday_status_cp'),
                'type': 'remove',
                'date_from': '2018-08-07 00:00:01',
                'date_to': '2018-08-17 23:59:59',
                'allocation_id': self.allocation.id,
                'number_of_days_temp': 9,
            }
        )

    def test_get_remaining_days(self):
        self.fjouatte2._get_remaining_days()
        self.assertEquals(self.fjouatte2.remaining_leaves, 0.0)
        self.fjouatte._get_remaining_days()
        self.assertEquals(self.fjouatte.remaining_leaves, 16)
