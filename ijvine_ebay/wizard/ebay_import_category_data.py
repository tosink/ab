# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import api, fields, models, _

from odoo import tools, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from ..ebaysdk.trading import Connection as Trading


class ImportEbayCategories(models.TransientModel):
	_name = "import.ebay.categories"
	_description = "Import Ebay Caetegories"
	_output_selector = "CategoryCount,CategoryArray.Category.CategoryName,CategoryArray.Category.CategoryParentID,CategoryArray.Category.CategoryLevel,CategoryArray.Category.CategoryID"

	@api.model
	def _FetchEbayCategories(self, api):
		message = ""
		status = True
		result = False
		total = 0
		context = dict(self._context or {})
		try:
			callData = {
				'DetailLevel': 'ReturnAll',
				'CategorySiteID': context['ebay_cat_site_id'],
				'LevelLimit': context['levellimit'],
			}
			if context.get('ebay_parent_category_id'):
				callData['CategoryParent'] = str(
					context['ebay_parent_category_id'])
			response = api.execute('GetCategories', callData)

			result_dict = response.dict()
			if self.channel_id.debug == 'enable':
				_logger.info('--------------Category Response------------%r',result_dict)
			if result_dict['Ack'] == 'Success':
				if result_dict.get('CategoryArray'):
					result = result_dict.get('CategoryArray').get('Category')
					total = result_dict.get('CategoryCount')
				else:
					status = False
					message = "No Child Categories found for this Category."
			else:
				message = message + 'STATUS : %s <br>' % result_dict['Ack']
				message = message + \
					'ErrorCode : %s <br>' % result_dict['Errors']['ErrorCode']
				message = message + 'ShortMessage : %s <br>' % result_dict[
					'Errors']['ShortMessage']
				message = message + "LongMessage: %s <br>" % result_dict[
					'Errors']['LongMessage']
				status = False
		except Exception as e:
			message = "Error in Fetching Categories: %s" % e
			status = False
			_logger.info('----------Exception in Fetching Categories-------------------%r',e)
		return {'status': status, 'message': message, 'result': result, 'total': total}

	@api.model
	def _CreateOdooFeeds(self, EbayCategories):
		message = ""
		status = True
		create_ids = []
		update_ids = []
		context = dict(self._context or {})
		CategFeedObj = self.env['category.feed']
		if context.get('channel_id'):
			ChannelID = context['channel_id']
		else:
			ChannelID = self.channel_id
		if type(EbayCategories) != list:
			EbayCategories = [EbayCategories]
		for ebay_category in EbayCategories:
			obj_exist = CategFeedObj.search(
				[('store_id', '=', ebay_category['CategoryID'])], limit=1)
			cat_dict = {
				'name': ebay_category['CategoryName'],
				'store_id': ebay_category['CategoryID'],
				'channel_id': ChannelID.id,
				'channel': 'ebay'
			}
			if ebay_category['CategoryID'] != ebay_category['CategoryParentID']:
				cat_dict['parent_id'] = ebay_category['CategoryParentID']
			if ebay_category.get('LeafCategory'):
				cat_dict['leaf_category'] = True
			if ChannelID.debug =='enable':
				_logger.info('------Category Feed-created---Id =----%r',ebay_category['CategoryID'])
			if not obj_exist:
				created_id = CategFeedObj.create(cat_dict)
				# self._cr.commit
				create_ids.append(created_id)
			else:
				res = obj_exist.write(cat_dict)
				if res:
					obj_exist.state = 'update'
					update_ids.append(obj_exist)
		return dict(
			create_ids=create_ids,
			update_ids=update_ids,
		)

	def import_now(self):
		final_message = ""
		status = True
		create_ids, update_ids, map_create_ids, map_update_ids = [], [], [], []
		context = dict(self._context or {})
		for record in self:
			api_obj = record.env["multi.channel.sale"]._get_api(
				record.channel_id, 'Trading')
			if api_obj['status']:
				DefaultData = record.env[
					"multi.channel.sale"]._get_default_data(record.channel_id)
				context['levellimit'] = record.levellimit
				context['ebay_cat_site_id'] = DefaultData[
					'data']['ebay_cat_site_id']
				if record.ebay_parent_category:
					context[
						'ebay_parent_category_id'] = record.ebay_parent_category.store_category_id
				FetchedEbayCategories = record.with_context(
					context)._FetchEbayCategories(api_obj['api'])
				if FetchedEbayCategories['status']:
					feed_res = record.with_context(context)._CreateOdooFeeds(
						FetchedEbayCategories['result'])
					post_res = record.env['channel.operation'].post_feed_import_process(
						self.channel_id, feed_res)
					create_ids += post_res.get('create_ids')
					update_ids += post_res.get('update_ids')
					map_create_ids += post_res.get('map_create_ids')
					map_update_ids += post_res.get('map_update_ids')
				else:
					final_message = FetchedEbayCategories['message']
			else:
				final_message = api_obj['message']
		final_message += self.env['multi.channel.sale'].get_feed_import_message(
			'category', create_ids, update_ids, map_create_ids, map_update_ids
		)
		return self.env['multi.channel.sale'].display_message(final_message)

	@api.model
	def _default_channel_id(self):
		return self._context['active_id']

	ebay_parent_category = fields.Many2one(
		comodel_name='channel.category.mappings',
		string='Ebay Parent Category',
		domain=[('ecom_store','=','ebay'),('leaf_category','=',False)])
	detaillevel = fields.Char(
		string='Default Detail Level',
		size=50,
		required=1,
		readonly=1,
		invisible=0,
		default='ReturnAll')
	levellimit = fields.Integer(
		string='Default Level Limit',
		required=1,
		default=2)
	channel_id = fields.Many2one(
		comodel_name='multi.channel.sale',
		string='Channel ID',
		required=1,
		readonly=1,
		default=_default_channel_id,
		help="Channel id which you want to use for importing the ebay categories")
