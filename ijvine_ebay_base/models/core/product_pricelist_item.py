# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models
from logging import getLogger

_logger = getLogger(__name__)


class PricelistItem(models.Model):
	_inherit = 'product.pricelist.item'

	def write(self, vals):
		for rec in self:
			rec.product_tmpl_id.channel_mapping_ids.write({'need_sync': 'yes'})
			rec.product_id.channel_mapping_ids.write({'need_sync': 'yes'})
			rec.product_id.product_tmpl_id.channel_mapping_ids.write({'need_sync': 'yes'})
		return super().write(vals)
