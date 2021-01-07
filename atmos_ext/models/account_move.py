from odoo import fields, models, api, SUPERUSER_ID, _
import pdb


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_scheme_id = fields.Many2one('atmos.sale.schemes', 'Sale Scheme', tracking=True, index=True)

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
    net_total = fields.Float("Net Total")


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
