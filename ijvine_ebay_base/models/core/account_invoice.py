# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models
import itertools


class AccountInvoice(models.Model):
	_inherit = 'account.move'

	def action_invoice_paid(self):
		self.ijvine_pre_confirm_paid()
		result = super(AccountInvoice,self).action_invoice_paid()
		self.ijvine_post_confirm_paid(result)
		return result

	def ijvine_get_invoice_order(self,invoice):
		data = map(
			lambda line_id: list(set(line_id.sale_line_ids.mapped('order_id'))),
			invoice.invoice_line_ids
		)
		return list(itertools.chain(*data))

	def ijvine_pre_confirm_paid(self):
		for invoice in self:
			for order_id in invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id'):
				mapping_ids = order_id.channel_mapping_ids
				if mapping_ids:
					channel_id = mapping_ids[0].channel_id
					if hasattr(channel_id,'%s_pre_confirm_paid'%channel_id.channel) and channel_id.sync_invoice:
						getattr(channel_id,'%s_pre_confirm_paid'%channel_id.channel)(invoice,mapping_ids)

	def ijvine_post_confirm_paid(self,result):
		for invoice in self:
			for order_id in invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id'):
				mapping_ids = order_id.channel_mapping_ids
				if mapping_ids:
					channel_id = mapping_ids[0].channel_id
					if hasattr(channel_id,'%s_post_confirm_paid'%channel_id.channel) and channel_id.sync_invoice:
						getattr(channel_id,'%s_post_confirm_paid'%channel_id.channel)(invoice,mapping_ids,result)
