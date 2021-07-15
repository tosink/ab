from odoo import fields, models, api


class BookingTeam(models.Model):
    _name = 'booking.team'
    _description = 'booking team'
    _rec_name = 'team_name'

    team_name = fields.Char(required=True)
    team_leader = fields.Many2one('hr.employee')
    employee_ids = fields.One2many('hr.employee', 'team_id')
    equipment_ids = fields.One2many('product.product', 'team_id')


class BookingTeamEmployee(models.Model):
    _inherit = "hr.employee"

    team_id = fields.Many2one('booking.team')
