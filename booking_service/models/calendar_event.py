from odoo import fields, models, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    equipment_ids = fields.Many2many('product.product', string='Equipments')
    employee_partner_id = fields.Integer()

