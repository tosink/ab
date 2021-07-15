from odoo import fields, models, api


class BookingEquipment(models.Model):
    _inherit = "product.template"

    team_id = fields.Many2one('booking.team')
    is_equipment = fields.Boolean()