# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ExportAttribute(models.TransientModel):
	_name = 'export.attributes'
	_description = 'Export Attribute'
	_inherit = 'export.operation'

	attribute_ids = fields.Many2many(
		comodel_name = 'product.attribute',
		string       = 'Attribute(s)'
	)

	@api.model
	def default_get(self,fields):
		res = super(ExportAttribute,self).default_get(fields)
		if not res.get('attribute_ids') and self._context.get('active_model')=='product.attribute':
			res['attribute_ids'] = self._context.get('active_ids')
		return res
