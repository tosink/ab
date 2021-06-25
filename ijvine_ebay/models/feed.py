# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)
class ProductVaraintFeed(models.Model):
	_inherit = 'product.variant.feed'

	ebay_description_html = fields.Text(
	string='Ebay HTML Description'
	)

	@api.model
	def get_product_fields(self):
		res = super(ProductVaraintFeed, self).get_product_fields()
		res+=['ebay_description_html']
		return res
		

