import anybox.testing.datetime # noqa
from anybox.testing.openerp import SharedSetupTransactionCase
from datetime import datetime
from openerp.exceptions import ValidationError


class TestHrHolidaysStatus(SharedSetupTransactionCase):

    _data_files = ('data.xml', )
    _module_ns = 'tests'

    def setUp(self):
        super(TestHrHolidaysStatus, self).setUp()
        self.cp = self.env.ref('tests.holiday_status_cp')

    def test_name_get(self):
        res = self.cp.name_get()
        self.assertEquals(res, [(self.cp.id, 'CP')])
