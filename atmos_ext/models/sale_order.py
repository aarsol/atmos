from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import pdb


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_scheme_id = fields.Many2one('atmos.sale.schemes', 'Sale Scheme', tracking=True, index=True)
    show_apply_scheme = fields.Boolean('Show Apply Scheme   ', compute='_compute_apply_scheme', store=True, default=False)
    disc1 = fields.Float('Com-1')
    disc2 = fields.Float('Com-2')
    disc3 = fields.Float('Com-3')
    disc4 = fields.Float('Com-4')
    disc5 = fields.Float('Com-5')

    subtotal1 = fields.Float('Sub-Total1')
    subtotal2 = fields.Float('Sub-Total2')
    subtotal3 = fields.Float('Sub-Total3')
    subtotal4 = fields.Float('Sub-Total4')
    subtotal5 = fields.Float('Sub-Total5')

    net_total = fields.Float("Net Total", compute='_compute_net_total', store=True)
    salesman_id = fields.Many2one('hr.employee', 'Salesman')

    def action_apply_scheme(self):
        for rec in self:
            if rec.sale_scheme_id and rec.order_line:
                sale_order_lines = rec.order_line
                for line in sale_order_lines:
                    line.actual_qty = rec.sale_scheme_id.actual_qty * line.scheme_factor
                    line.discount_qty = rec.sale_scheme_id.discount_qty * line.scheme_factor

                if rec.sale_scheme_id.scheme_discount_ids:
                    rec.calc_discounts()
                rec.show_apply_scheme = False

    def calc_discounts(self):
        for rec in self:
            for discount_id in rec.sale_scheme_id.scheme_discount_ids.sorted(key=lambda d: d.priority):
                if discount_id.priority=='1':
                    if discount_id.discount_type=='Fixed':
                        rec.disc1 = discount_id.discount_value
                        rec.subtotal1 = rec.amount_total - discount_id.discount_value
                    if discount_id.discount_type=='Percentage':
                        rec.disc1 = round((rec.amount_total * (discount_id.discount_value / 100)), 2)
                        rec.subtotal1 = rec.amount_total - rec.disc1
                    rec.net_total = rec.subtotal1

                if discount_id.priority=='2':
                    if discount_id.discount_type=='Fixed':
                        rec.disc2 = discount_id.discount_value
                        rec.subtotal2 = rec.subtotal1 - discount_id.discount_value
                    if discount_id.discount_type=='Percentage':
                        rec.disc2 = round((rec.subtotal1 * (discount_id.discount_value / 100)), 2)
                        rec.subtotal2 = rec.subtotal1 - rec.disc2
                    rec.net_total = rec.subtotal2

                if discount_id.priority=='3':
                    if discount_id.discount_type=='Fixed':
                        rec.disc3 = discount_id.discount_value
                        rec.subtotal3 = rec.subtotal2 - discount_id.discount_value
                    if discount_id.discount_type=='Percentage':
                        rec.disc3 = round((rec.subtotal2 * (discount_id.discount_value / 100)), 2)
                        rec.subtotal3 = rec.subtotal2 - rec.disc3
                    rec.net_total = rec.subtotal3

                if discount_id.priority=='4':
                    if discount_id.discount_type=='Fixed':
                        rec.disc4 = discount_id.discount_value
                        rec.subtotal4 = rec.subtotal3 - discount_id.discount_value
                    if discount_id.discount_type=='Percentage':
                        rec.disc4 = round((rec.subtotal3 * (discount_id.discount_value / 100)), 2)
                        rec.subtotal4 = rec.subtotal3 - rec.disc4
                    rec.net_total = rec.subtotal4

                if discount_id.priority=='5':
                    if discount_id.discount_type=='Fixed':
                        rec.disc5 = discount_id.discount_value
                        rec.subtotal5 = rec.subtotal4 - discount_id.discount_value
                    if discount_id.discount_type=='Percentage':
                        rec.disc5 = round((rec.subtotal4 * (discount_id.discount_value / 100)), 2)
                        rec.subtotal5 = rec.subtotal4 - rec.disc5
                    rec.net_total = rec.subtotal5

    @api.depends('sale_scheme_id')
    def _compute_apply_scheme(self):
        for rec in self:
            if rec.sale_scheme_id:
                rec.show_apply_scheme = 'True'
            else:
                rec.show_apply_scheme = False

    def action_recompute_scheme(self):
        for rec in self:
            rec.action_apply_scheme()

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'sale_scheme_id': self.sale_scheme_id and self.sale_scheme_id.id or False,
            'disc1': self.disc1,
            'disc2': self.disc2,
            'disc3': self.disc3,
            'disc4': self.disc4,
            'disc5': self.disc5,
            'subtotal1': self.subtotal1,
            'subtotal2': self.subtotal2,
            'subtotal3': self.subtotal3,
            'subtotal4': self.subtotal4,
            'subtotal5': self.subtotal5,
            'net_total': self.net_total,
        }
        return invoice_vals

    @api.depends('amount_total', 'subtotal1', 'subtotal2', 'subtotal3', 'subtotal4', 'subtotal5')
    def _compute_net_total(self):
        for rec in self:
            if rec.subtotal5 > 0:
                rec.net_total = rec.subtotal5
                break
            elif rec.subtotal4 > 0:
                rec.net_total = rec.subtotal4
                break
            elif rec.subtotal3 > 0:
                rec.net_total = rec.subtotal3
                break
            elif rec.subtotal2 > 0:
                rec.net_total = rec.subtotal2
                break
            elif rec.subtotal1 > 0:
                rec.net_total = rec.subtotal1
                break
            else:
                rec.net_total = rec.amount_total


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0, compute='_compute_total_qty', store=True)
    discount_qty = fields.Integer('Bonus Qty')
    actual_qty = fields.Integer('Actual Qty', default=1)
    scheme_factor = fields.Integer('Factor')

    @api.depends('discount_qty', 'actual_qty')
    def _compute_total_qty(self):
        for rec in self:
            rec.product_uom_qty = rec.actual_qty + rec.discount_qty

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            scheme_discount = line.discount_qty * line.price_unit
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty - line.discount_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()

        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
            'actual_qty': self.actual_qty,
            'discount_qty': self.discount_qty,
            'retail_price': self.price_unit,
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res
