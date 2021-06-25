# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from ...ApiTransaction import Transaction

from odoo import api,fields,models

class ExportOperation(models.TransientModel):
	_name = 'export.operation'
	_description = 'Export Operation'
	_inherit = 'channel.operation'

	operation=fields.Selection(
		selection=[
			('export','Export'),
			('update','Update')
		],
		default ='export',
		required=True
	)

	object = fields.Selection(
		selection=[
			('product.category','Category'),
			('product.template','Product Template'),
		],
		default='product.category',
	)

	def export_button(self):
		if self._context.get('active_model','multi.channel.sale') == 'multi.channel.sale':
			return Transaction(channel=self.channel_id).export_data(
				object = self.object,
				object_ids = self.env[self.object].search([]).ids,
				operation = 'export',
			)
		else:
			return Transaction(channel=self.channel_id).export_data(
				object = self._context.get('active_model'),
				object_ids = self._context.get('active_ids'),
				operation = self.operation,
			)
