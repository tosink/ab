# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class WizardMessage(models.TransientModel):
	_name = "wizard.message"
	_description = "Message Wizard"

	text = fields.Text(string='Message')

	@api.model
	def genrated_message(self,message,name='Message/Summary'):
		res = self.create({'text': message})
		return {
			'name'     : name,
			'type'     : 'ir.actions.act_window',
			'res_model': 'wizard.message',
			'view_mode': 'form',
			'target'   : 'new',
			'res_id'   : res.id,
		}
