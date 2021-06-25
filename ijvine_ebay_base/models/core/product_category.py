# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import fields,models


class ProductCategory(models.Model):
	_inherit = 'product.category'

	channel_mapping_ids = fields.One2many(
		string       = 'Mappings',
		comodel_name = 'channel.category.mappings',
		inverse_name = 'category_name',
		copy         = False
	)

	channel_category_ids = fields.One2many(
		string       = 'Channel Categories',
		comodel_name = 'extra.categories',
		inverse_name = 'category_id',
		copy         = False
	)

	def write(self, vals):
		for record in self:
			record.channel_mapping_ids.write({'need_sync': 'yes'})
			res = super(ProductCategory, record).write(vals)
		return res
