from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    voucher_type = fields.Selection([('BPV', 'BPV'),
                                     ('CPV', 'CPV'),
                                     ('BRV', 'BRV'),
                                     ('CRV', 'CRV'),
                                     ('JV', 'JV'),
                                     ('PV', 'PV'),
                                     ], string='Voucher Type')
    sale_scheme_id = fields.Many2one('atmos.sale.schemes', 'Sale Scheme', tracking=True, index=True)
    salesman_id = fields.Many2one('hr.employee', 'Salesman')

    disc1 = fields.Float('Com-1')
    disc2 = fields.Float('Com-2')
    disc3 = fields.Float('Com-3')
    disc4 = fields.Float('Com-4')
    disc5 = fields.Float('Com-5')
    total_disc = fields.Float('Total Disc', compute='_compute_total_disc', store=True)

    subtotal1 = fields.Float('Sub-Total1')
    subtotal2 = fields.Float('Sub-Total2')
    subtotal3 = fields.Float('Sub-Total3')
    subtotal4 = fields.Float('Sub-Total4')
    subtotal5 = fields.Float('Sub-Total5')
    net_total = fields.Float("Net Total")

    @api.depends('disc1', 'disc2', 'disc3', 'disc4', 'disc5')
    def _compute_total_disc(self):
        for rec in self:
            rec.total_disc = rec.disc1 + rec.disc2 + rec.disc3 + rec.disc4 + rec.disc5

    def _move_autocomplete_invoice_lines_values(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        '''
        self.ensure_one()
        for line in self.line_ids:
            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line.display_type and not line._origin:
                line.account_id = line._get_computed_account() or self.journal_id.default_account_id
            if line.product_id and not line._cache.get('name'):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            if line.partner_id!=self.partner_id.commercial_partner_id:
                line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = self.currency_id

        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

        values = self._convert_to_write(self._cache)

        # AARSOL
        if self.move_type=='out_invoice' and self.company_id.id==2 and self.total_disc > 0:
            if self.total_disc > 0:
                line_values = values.get('line_ids', False)
                if line_values:
                    discount = 0
                    for line_value in line_values:
                        if line_value==(6, 0, []):
                            continue
                        if line_value[2]['debit'] > 0:
                            line_value[2]['debit'] = line_value[2]['debit'] - self.total_disc
                            line_value[2]['sequence'] = 50

                com_dict = (0, 0, {
                    'account_id': 584,
                    'credit': 0,
                    'debit': self.total_disc,
                    'display_type': False,
                    'exclude_from_invoice_tab': True,
                    'name': 'Commission (Discount)',
                    'partner_id': self.partner_id and self.partner_id.id or False,
                    'price_subtotal': 0.0,
                    'price_unit': self.total_disc,
                    'quantity': 1.0,
                    'sequence': 20,
                })
                values['line_ids'].append(com_dict)

        values.pop('invoice_line_ids', None)
        return values

    def get_scheme_discount(self, scheme=False, priority=False):
        for rec in self:
            return_value = ''
            if scheme and priority:
                line = self.env['atmos.sale.schemes.discounts'].search([('scheme_id', '=', scheme.id),
                                                                        ('priority', '=', str(priority))])
                if line:
                    if not line.discount_type=='Fixed':
                        return_value = str(line.discount_value) + "%"
                    else:
                        return_value = line.discount_type
                    return return_value
        return return_value


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_qty = fields.Integer('Bonus Qty')
    actual_qty = fields.Integer('Actual Qty')
    retail_price = fields.Float('Retail Price')

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Scheme Discount
        scheme_discount = self.discount_qty * line_discount_price_unit
        subtotal = subtotal - scheme_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(line_discount_price_unit,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
