# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ExportAttributeValue(models.TransientModel):
	_name = 'export.attributes.value'
	_description = 'Export Attribute Value'
	_inherit = 'export.operation'

	attribute_value_ids = fields.Many2many(
		comodel_name = 'product.attribute.value',
		string       = 'Attribute(s)'
	)

	@api.model
	def default_get(self,fields):
		res = super(ExportAttributeValue,self).default_get(fields)
		if not res.get('attribute_value_ids') and self._context.get('active_model')=='product.attribute.value':
			res['attribute_value_ids'] = self._context.get('active_ids')
		return res
