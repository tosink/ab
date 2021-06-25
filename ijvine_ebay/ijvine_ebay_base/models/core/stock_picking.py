# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def action_done(self):
		self.ensure_one()
		self.ijvine_pre_do_transfer()
		result = super(StockPicking,self).action_done()
		self.ijvine_post_do_transfer(result)
		return result

	def ijvine_pre_do_transfer(self):
		if self.sale_id:
			mapping_ids = self.sale_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id,'%s_pre_do_transfer'%channel_id.channel) and channel_id.sync_shipment:
					getattr(channel_id,'%s_pre_do_transfer'%channel_id.channel)(self,mapping_ids)

	def ijvine_post_do_transfer(self,result):
		if self.sale_id:
			mapping_ids = self.sale_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id,'%s_post_do_transfer'%channel_id.channel) and channel_id.sync_shipment:
					getattr(channel_id,'%s_post_do_transfer'%channel_id.channel)(self,mapping_ids,result)
