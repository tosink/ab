# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models


class UpdateMappingWizard(models.TransientModel):
	_name        = 'update.mapping.wizard'
	_description = 'Update Mapping Wizard'

	need_sync = fields.Selection(
		selection=[
			('yes','Yes'),
			('no','No')
		],
		string   = 'Update Required',
		default  = 'yes',
		required = True
	)

	def save_status(self):
		for record in self:
			context    = dict(record._context)
			model      = self.env[context.get('active_model')]
			active_ids = model.browse(context.get('active_ids'))
			for active_id in active_ids:
				active_id.need_sync = record.need_sync
