from odoo import fields, models, api, SUPERUSER_ID, _
import pdb


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    driver_name = fields.Char('Driver')
    vehicle_number = fields.Char('Vehicle Number')
    driver_contact_no = fields.Char('Driver Contact')