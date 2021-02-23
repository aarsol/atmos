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

        total_receipt_amt = 0
        total_recovery_amt = 0
        total_commission_amt = 0

        if results:
            salesman = []
            for result in results:
                if not result['salesman_id']==None:
                    salesman.append(result['salesman_id'])
            salesman_ids = self.env['hr.employee'].search([('id', 'in', salesman)], order='id')
            for salesman_id in salesman_ids:
                receipt_total = 0
                recovery_total = 0
                bank_commission = 0

                invoices = self.env['account.move'].search([('salesman_id', '=', salesman_id.id), ('state', '!=', 'cancel')])
                for invoice in invoices:
                    receipt_total += invoice.total_disc

                    payment_recs = False
                    payment_recs = self.env['account.payment'].search([('ref', '=', invoice.name), ('state', '!=', 'cancel')])
                    # for payment_rec in payment_recs:
                    #     recovery_total += payment_rec.amount

                    if payment_recs:
                        recovery_total += invoice.total_disc

                if recovery_total > 0:
                    bank_commission = round(recovery_total * .03, 2)

                total_receipt_amt += receipt_total
                total_recovery_amt += recovery_total
                total_commission_amt += bank_commission

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
            'result': res,
            'total': {'total_receipt_amt': total_receipt_amt,
                      'total_recovery_amt': total_recovery_amt,
                      'total_commission_amt': total_commission_amt},
            'today': fields.Date.today().strftime('%b %d,%Y'),
            'date_from': fields.Date.from_string(date_from).strftime('%b %d, %Y'),
            'date_to': fields.Date.from_string(date_to).strftime('%b %d, %Y'),
        }
        return docargs
