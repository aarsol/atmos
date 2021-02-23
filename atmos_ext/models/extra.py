
# def action_apply_scheme(self):
#     for rec in self:
#         if rec.sale_scheme_id and rec.scheme_factor > 0:
#             if rec.order_line:
#                 sale_order_lines = rec.order_line
#                 section_data = {
#                     'display_type': 'line_section',
#                     'order_id': rec.id,
#                     'name': rec.sale_scheme_id.name,
#                 }
#                 section_rec = self.env['sale.order.line'].create(section_data)
#
#                 seq = 99
#                 for line in sale_order_lines:
#                     seq += 1
#                     line_data = {
#                         'product_id': line.product_id.id,
#                         'name': line.product_id.name,
#                         'product_uom_qty': rec.sale_scheme_id.discount_qty,
#                         'price_unit': 0,
#                         'order_id': rec.id,
#                         'sequence': seq,
#                     }
#                     new_line = self.env['sale.order.line'].create(line_data)
#             rec.show_apply_scheme = False