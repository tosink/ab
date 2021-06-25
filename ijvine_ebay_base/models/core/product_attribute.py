# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models


class ProductAttribute(models.Model):
	_inherit = 'product.attribute'

	@api.model
	def create(self, vals):
		if self._context.get('odoo_multi_attribute') or self._context.get('install_mode'):
			obj = self.search([('name','=ilike',vals.get('name').strip(' '))],limit=1)
			if obj:
				return obj
		return super(ProductAttribute, self).create(vals)
