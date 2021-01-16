import pdb
import time
import datetime
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class CommissionReportWiz(models.TransientModel):
    _name = 'commission.report.wiz'
    _description = 'Commission Report Wizard'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    date_from = fields.Date('From Date', default=fields.Date.today())
    date_to = fields.Date('To Date', default=fields.Date.today())

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        datas = {
            'ids': [],
            'model': 'commission.report.wiz',
            'form': data
        }
        return self.env.ref('atmos_ext.action_commission_report').with_context(landscape=True).report_action(self, data=datas, config=False)
