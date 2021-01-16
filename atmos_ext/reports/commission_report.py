from odoo import api, fields, models
import pdb


class CommissionReport(models.AbstractModel):
    _name = 'report.atmos_ext.commission_report'
    _description = 'Commission Report'

    @api.model
    def _get_report_values(self, docsid, data=None):
        employee_id = data['form']['employee_id'] and data['form']['employee_id'][0] or False
        date_from = data['form']['date_from'] and data['form']['date_from'] or False
        date_to = data['form']['date_to'] and data['form']['date_to'] or False
        res = []
        self.env.cr.execute("select distinct salesman_id from account_move where invoice_date >=%s and invoice_date <=%s and state !=%s;", (date_from, date_to, 'cancel'))
        results = self.env.cr.dictfetchall()
        if results:
            salesman = []
            for result in results:
                salesman.append(result['salesman_id'])
            salesman_ids = self.env['hr.employee'].search([('id', 'in', salesman)], order='id')
            for salesman_id in salesman_ids:
                receipt_total = 0
                recovery_total = 0
                bank_commission = 0

                invoices = self.env['account.move'].search([('salesman_id', '=', salesman_id.id), ('state', '!=', 'cancel')])
                for invoice in invoices:
                    receipt_total += invoice.net_total
                    payment_recs = self.env['account.payment'].search([('invoice_ids', 'in', [invoice.id]), ('state', '!=', 'cancel')])
                    for payment_rec in payment_recs:
                        recovery_total += payment_rec.amount
                if recovery_total > 0:
                    bank_commission = recovery_total * .03

                res.append({
                    'name': salesman_id.name,
                    'receipt_total': receipt_total,
                    'recovery_total': recovery_total,
                    'bank_commission': bank_commission,
                })

        report = self.env['ir.actions.report']._get_report_from_name('atmos_ext.commission_report')

        docargs = {
            'doc_ids': [],
            'doc_model': report.model,
            'data': data['form'],
            'result': res
        }
        return docargs
