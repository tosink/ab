# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BookingService(models.Model):
    _inherit = 'sale.order'

    is_booking = fields.Boolean(default=False)
    booking_team_id = fields.Many2one('booking.team')
    team_leader_id = fields.Many2one('hr.employee', related='booking_team_id.team_leader', readonly=False)
    team_emaployee_ids = fields.One2many(related='booking_team_id.employee_ids', readonly=False)
    team_equipment_ids = fields.One2many(related='booking_team_id.equipment_ids', readonly=False)
    booking_start = fields.Datetime()
    booking_end = fields.Datetime()

    def action_check_calendar(self):
        events = self.env['calendar.event'].search([])
        attendants = []
        if self.team_leader_id:
            employees = [emp.id for emp in self.team_emaployee_ids if self.team_emaployee_ids]
            employees.append(self.team_leader_id.id)
            partners = self.env['hr.employee'].browse(employees).mapped('user_id').mapped('partner_id')
            for event in events:
                if self.booking_start and self.booking_end:
                    if event.start < self.booking_start < event.stop:
                        for partner in partners:
                            if partner.id in event.partner_ids.ids:
                                attendants.append(partner.name)
                        if attendants:
                            raise ValidationError('{} has an event on {}'.format(','.join(attendants), self.booking_start))
                        else:
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'type': 'success',
                                    'message': "Everyone is available for the booking!",
                                }
                            }

