from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import pdb


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_scheme_id = fields.Many2one('atmos.sale.schemes', 'Sale Scheme', tracking=True, index=True)
    show_apply_scheme = fields.Boolean('Show Apply Scheme   ', compute='_compute_apply_scheme', store=True, default=False)
    scheme_factor = fields.Integer('Factor')

    def action_apply_scheme(self):
        for rec in self:
            if rec.sale_scheme_id and rec.scheme_factor > 0:
                if rec.order_line:
                    sale_order_lines = rec.order_line
                    for line in sale_order_lines:
                        line.actual_qty = rec.sale_scheme_id.actual_qty * rec.scheme_factor
                        line.discount_qty = rec.sale_scheme_id.discount_qty * rec.scheme_factor
                rec.show_apply_scheme = False

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
            'scheme_factor': self.scheme_factor,
        }
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0, compute='_compute_total_qty', store=True)
    discount_qty = fields.Integer('Bonus Qty')
    actual_qty = fields.Integer('Actual Qty', default=1)

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
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res


class SaleSchemes(models.Model):
    _name = 'atmos.sale.schemes'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = 'Sale Schemes'

    name = fields.Char('Name', required=True, tracking=True, index=True)
    code = fields.Char('Code', tracking=True)
    sequence = fields.Integer('Sequence')
    company_id = fields.Many2one('res.company', 'Company', tracking=True, index=True, default=lambda self: self.env.user.company_id.id)
    active = fields.Boolean('Active', default=True, tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True, index=True)
    actual_qty = fields.Integer('Actual Qty')
    discount_qty = fields.Integer('Discounted Qty')
    state = fields.Selection([('draft', 'Draft'),
                              ('lock', 'Locked')
                              ], string='Status', default='draft', tracking=True)

    @api.model
    def create(self, values):
        res = super().create(values)
        return res

    def unlink(self):
        return super(SaleSchemes, self).unlink()

    def action_lock(self):
        self.state = 'lock'

    def action_unlock(self):
        self.state = 'draft'

    @api.constrains('name')
    def name_constrains(self):
        for rec in self:
            if rec.name:
                duplicate_record = self.env['atmos.sale.schemes'].search([('name', '=', rec.name), ('id', '!=', rec.id)])
                if duplicate_record:
                    raise UserError(_('Duplicate Names are not Allowed, Please change the Name of Record'))

    @api.constrains('actual_qty', 'discount_qty')
    def qty_constrains(self):
        for rec in self:
            if rec.actual_qty==0:
                raise UserError(_('Actual Qty Should be Greater then Zero'))
            if rec.discount_qty==0:
                raise UserError(_('Discounted Qty Should be Greater then Zero'))

            if 0 < rec.actual_qty < rec.discount_qty and rec.discount_qty > 0:
                raise UserError(_('Discounted Qty should not be Greater then Actual Qty. Here Actual Qty is %s and discounted Qty is %s') % (rec.actual_qty, rec.discount_qty))
