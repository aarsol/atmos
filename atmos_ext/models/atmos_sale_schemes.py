from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
import pdb


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_scheme_id = fields.Many2one('atmos.sale.schemes', 'Sale Scheme', tracking=True, index=True)
    show_apply_scheme = fields.Boolean('Show Apply Scheme   ', compute='_compute_apply_scheme', store=True, default=False)

    def action_apply_scheme(self):
        for rec in self:
            if rec.sale_scheme_id:
                if rec.order_line:
                    sale_order_lines = rec.order_line
                    section_data = {
                        'display_type': 'line_section',
                        'order_id': rec.id,
                        'name': rec.sale_scheme_id.name,
                    }
                    section_rec = self.env['sale.order.line'].create(section_data)

                    seq = 99
                    for line in sale_order_lines:
                        seq += 1
                        line_data = {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_uom_qty': rec.sale_scheme_id.discount_qty,
                            'price_unit': 0,
                            'order_id': rec.id,
                            'sequence': seq,
                        }
                        new_line = self.env['sale.order.line'].create(line_data)
                rec.show_apply_scheme = False

    @api.depends('sale_scheme_id')
    def _compute_apply_scheme(self):
        for rec in self:
            if rec.sale_scheme_id:
                rec.show_apply_scheme = 'True'
            else:
                rec.show_apply_scheme = False


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
