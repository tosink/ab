# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ExportTemplate(models.TransientModel):
	_name = 'export.templates'
	_description = 'Export Template'
	_inherit = 'export.operation'

	product_tmpl_ids = fields.Many2many(
		comodel_name = 'product.template',
		string       = 'Product Template(s)',
	)
	sku_sequence_id = fields.Many2one(
		related = 'channel_id.sku_sequence_id',
		string  = 'SKU Sequence'
	)

	def export_odoo_products(self):
		if hasattr(self,'export_%s_templates'%self.channel_id.channel):
			return getattr(self,'export_%s_templates'%self.channel_id.channel)()

	def update_odoo_products(self):
		if hasattr(self,'update_%s_templates'%self.channel_id.channel):
			return getattr(self,'update_%s_templates'%self.channel_id.channel)()

	@api.model
	def default_get(self,fields):
		res = super(ExportTemplate,self).default_get(fields)
		if not res.get('product_tmpl_ids') and self._context.get('active_model')=='product.template':
			res['product_tmpl_ids'] = self._context.get('active_ids')
		return res
