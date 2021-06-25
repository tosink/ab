# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	channel_mapping_ids = fields.One2many(
		string='Mappings',
		comodel_name='channel.order.mappings',
		inverse_name='order_name',
		copy=False
	)

	def action_cancel(self):
		self.ensure_one()
		self.ijvine_pre_cancel()
		result = super(SaleOrder, self).action_cancel()
		self.ijvine_post_cancel(result)
		return result

	def ijvine_pre_cancel(self):
		for order_id in self:
			mapping_ids = order_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id, '%s_pre_cancel_order' % channel_id.channel) and channel_id.sync_cancel:
					getattr(channel_id, '%s_pre_cancel_order' % channel_id.channel)(self, mapping_ids)

	def ijvine_post_cancel(self,result):
		for order_id in self:
			mapping_ids = order_id.channel_mapping_ids
			if mapping_ids:
				channel_id = mapping_ids[0].channel_id
				if hasattr(channel_id, '%s_post_cancel_order' % channel_id.channel) and channel_id.sync_cancel:
					getattr(channel_id, '%s_post_cancel_order' % channel_id.channel)(self, mapping_ids, result)
