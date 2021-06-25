# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ExportCategory(models.TransientModel):
	_name = 'export.categories'
	_description = 'Export Category'
	_inherit = 'export.operation'

	category_ids = fields.Many2many(
		comodel_name = 'product.category',
		string       = 'Category'
	)

	@api.model
	def default_get(self,fields):
		res = super(ExportCategory,self).default_get(fields)
		if not res.get('category_ids') and self._context.get('active_model')=='product.category':
			res['category_ids'] = self._context.get('active_ids')
		return res
