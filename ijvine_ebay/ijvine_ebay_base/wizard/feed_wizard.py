# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################

from odoo import api,fields,models,_
from logging import getLogger
_logger=getLogger(__name__)


class FeedSyncWizard(models.TransientModel):
	_name='feed.sync.wizard'
	_description='Evaluate Feeds Wizard'

	channel_id=fields.Many2one(
		comodel_name='multi.channel.sale',
		string='Channel ID',
		required=True,
		readonly=True,
		domain=[('state','=','validate')]
	)

	feed_type=fields.Selection(
		selection=[
			('product.feed','Product'),
			('category.feed','Category'),
			('order.feed','Order'),
			('partner.feed','Partner'),
			('shipping.feed','Shipping')
		],
		string='Feed Type',
		required=True
	)

	def action_sync_feed(self):
		self.ensure_one()
		res = self.env[self.feed_type].search(
			[
				('channel_id','=',self.channel_id.id),
				('state','!=','done'),
			]
		).with_context(channel_id=self.channel_id).import_items()
		return res
