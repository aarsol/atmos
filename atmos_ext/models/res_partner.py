from odoo import fields, models, api, SUPERUSER_ID, _
import pdb


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_code = fields.Char('Code')