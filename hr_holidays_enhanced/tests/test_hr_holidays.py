from anybox.testing.openerp import SharedSetupTransactionCase
from openerp.addons.hr_holidays_enhanced.models.hr_holidays import HrHolidays
from openerp.exceptions import Warning, ValidationError


class TestHrHolidays(SharedSetupTransactionCase):

    _data_files = ('data.xml', )
    _module_ns = 'tests'

    def setUp(self):
        super(TestHrHolidays, self).setUp()
        self.hr_holidays = self.env['hr.holidays']
        self.allocation = self.hr_holidays.create(
            {
                'employee_id': self.ref('tests.employee_fjouatte'),
                'holiday_status_id': self.ref('tests.holiday_status_cp'),
                'type': 'add',
                'date_from': '2018-06-01 00:00:01',
                'date_to': '2019-05-31 23:59:59',
                'number_of_days_temp': 25,
            }
        )
        self.leave = self.hr_holidays.create(
            {
                'employee_id': self.ref('tests.employee_fjouatte'),
                'holiday_status_id': self.ref('tests.holiday_status_cp'),
                'type': 'remove',
                'date_from': '2018-08-07 00:00:01',
                'date_to': '2018-08-17 23:59:59',
                'allocation_id': self.allocation.id,
                'number_of_days_temp': 9,
            }
        )

    def test_get_number_of_days(self):
        res = self.hr_holidays._get_number_of_days('2018-08-07 00:00:01', '2018-08-17 23:59:59')
        self.assertEquals(res, 8)
        res = self.hr_holidays._get_number_of_days('2018-08-07 00:00:01', '2018-08-07 23:59:59')
        self.assertEquals(res, 0)

    def test_onchange_date_from(self):
        self.leave.onchange_date_from()
        self.assertEquals(self.leave.number_of_days_temp, 9)
        self.leave.date_from = '2018-08-06 00:00:01'
        self.leave.onchange_date_from()
        self.assertEquals(self.leave.number_of_days_temp, 10)
        """
        with patch('openerp.addons.hr_holidays_enhanced.models.hr_holidays.HrHolidays') as MockClass:
            holiday = MockClass.return_value
            holiday.date_to = False
            holiday.onchange_date_from()
        setattr(holiday, 'date_from', None)
        self.assertEquals(holiday.number_of_days_temp, 1)
        self.assertEquals(holiday.date_to, '2018-08-06 08:00:01')
        """

    def test_get_remaining_days(self):
        remaining_days = self.leave.get_remaining_days()
        self.assertEquals(remaining_days, 16)
        self.leave.date_to = '2018-08-18 23:59:59'
        self.leave.onchange_date_to()
        remaining_days = self.leave.get_remaining_days()
        self.assertEquals(remaining_days, 16)
        self.leave.date_to = '2018-08-20 23:59:59'
        self.leave.onchange_date_to()
        remaining_days = self.leave.get_remaining_days()
        self.assertEquals(remaining_days, 15)

    def test_check_date(self):
        res = self.leave._check_date()
        self.assertTrue(res)
        res = self.allocation._check_date()
        self.assertTrue(res)
        with self.assertRaises(ValidationError):
            self.hr_holidays.create(
                {
                    'employee_id': self.ref('tests.employee_fjouatte'),
                    'holiday_status_id': self.ref('tests.holiday_status_cp'),
                    'type': 'remove',
                    'date_from': '2018-08-06 00:00:01',
                    'date_to': '2018-08-07 23:59:59',
                    'allocation_id': self.allocation.id,
                    'number_of_days_temp': 2,
                }
            )

    def test_check_holidays(self):
        res = self.leave._check_holidays()
        self.assertTrue(res)
        res = self.allocation._check_holidays()
        self.assertTrue(res)
        with self.assertRaises(ValidationError):
            self.leave.date_to = '2018-09-20 23:59:59'
            self.leave.onchange_date_to()

