# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import api, fields, models, _
import base64  # file encode
import urllib.request # file download from url
from odoo import tools, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from xml.dom.minidom import parseString
import logging
import re
import urllib.parse
from ..ebaysdk.trading import Connection as Trading
_logger = logging.getLogger(__name__)
def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.

	try:
		return urllib.parse(text.encode('utf8'))
	except Exception as e:
		return text



class ImportEbayProducts(models.TransientModel):
	_name = "import.ebay.products"
	_description="Import Ebay Products"
	_output_selector = "HasMoreItems,Ack,PageNumber,Errors,PaginationResult,ItemArray.Item.Title,ItemArray.Item.ItemID,ItemArray.Item.Description,ItemArray.Item.PrimaryCategory,ItemArray.Item.SellingStatus.CurrentPrice.value,ItemArray.Item.Quantity,ItemArray.Item.Variations"

	@api.model
	def _CalculateSalesTax(self, ebay_tax):
		TaxOBj = self.env['account.tax']
		MapObj = self.env['channel.account.mappings']
		amount = float(ebay_tax['SalesTaxPercent'])
		name = 'Tax ' + str(amount) + '%'
		exists = MapObj.search([('name', '=', name)])
		tax_id = 0
		if exists:
			tax_id = exists[0].OdooTaxID
		else:
			if amount != 0.0:
				tax_data = {
					'name': name,
					'amount_type': 'percent',
					'amount': float(ebay_tax['SalesTaxPercent']),
					'type_tax_use': 'sale',
					'description': ebay_tax['SalesTaxPercent'] + '%'
				}
				tax_id = TaxOBj.create(tax_data).id
				if tax_id:
					MapObj.create({'StoreTaxValue': ebay_tax[
						'SalesTaxPercent'], 'OdooTaxID': tax_id, 'TaxName': tax_id, 'name': name})
		return tax_id

	@api.model
	def CreateOdooVariantFeed(self, EbayProdData=False,mapping_id=False):
		context = dict(self._context or {})
		variant_list = []
		context['ebay_variant'] = EbayProdData['Variations']
		if EbayProdData['Variations'].get('Variation'):
			variants = EbayProdData['Variations']['Variation']
			if isinstance(variants, (dict)):
				variants = [variants]
			for variant_line in variants:
				name_vale_list = variant_line[
					'VariationSpecifics']['NameValueList']
				attr_string = self._CreateAttributeString(variant_line)
				if attr_string:
					varinat_store_id = attr_string
				else:
					varinat_store_id = 'No Varinats'
				if isinstance(name_vale_list, (dict)):
					name_vale_list = [name_vale_list]
				name_value = []
				qty_available = int(variant_line.get('Quantity')) - int(variant_line.get('SellingStatus').get('QuantitySold'))
				for nm in name_vale_list:
					name_value.append( {'name': nm['Name'], 'value': nm['Value']})
				if mapping_id and mapping_id.feed_variants:
					feed_varaint_ids = mapping_id.feed_variants.read(['store_id'])
					vs_ids = []
					for vs_id in feed_varaint_ids:
						vs_ids.append(vs_id.get('store_id'))
					
					if varinat_store_id in vs_ids:
						f_variant_id =  mapping_id.feed_variants.search([('store_id','=',varinat_store_id)],limit=1)
						
						variant_list.append((1, f_variant_id.id, {'name_value': name_value, 'list_price': variant_line.get('StartPrice').get('value'), 'qty_available': qty_available, 'store_id': varinat_store_id,'default_code':variant_line.get('SKU')}))
					else:
						variant_list.append((0, 0, {'name_value': name_value, 'list_price': variant_line.get('StartPrice').get('value'), 'qty_available': qty_available, 'store_id': varinat_store_id,'default_code':variant_line.get('SKU')}))
				else:
					variant_list.append((0, 0, {'name_value': name_value, 'list_price': variant_line.get('StartPrice').get('value'), 'qty_available': qty_available, 'store_id': varinat_store_id,'default_code':variant_line.get('SKU')}))
		return variant_list

	@api.model
	def GetEbayProductDescription(self, description):

		if description:
			desc = re.sub('<[^<]+?>', '', description)
			desc = re.sub(r'&(.*?);', '', desc)
			description = desc
		else:
			description = 'No Description'
		return description

	@api.model
	def GetOdooTemplateData(self, EbayProdData, ChannelID):
		description = self.GetEbayProductDescription(
			EbayProdData['Description'])
		qty_available = int(EbayProdData.get('Quantity')) - int(EbayProdData.get('SellingStatus').get('QuantitySold'))
		template_data = {
			'name': _unescape(EbayProdData.get('Title')),
			'list_price': EbayProdData.get('SellingStatus').get('CurrentPrice').get('value'),
			'store_id': EbayProdData.get('ItemID'),
			'channel_id': ChannelID.id,
			'channel': 'ebay',
			'qty_available': qty_available,
			'default_code':EbayProdData.get('SKU')
		}
		if ChannelID.ebay_use_html_description:
			template_data ['ebay_description_html'] = description
		else:
			template_data ['description_sale'] = description
		return template_data

	@api.model
	def _CreateOdooFeed(self, EbayProdData):
		context = dict(self._context or {})
		if isinstance(EbayProdData, (list)):
			EbayProdData = EbayProdData[0]
		FeedObj = self.env['product.feed']
		mapping_id = FeedObj.search( [('store_id', '=', EbayProdData['ItemID'])])
		status = False
		FeedsCreated = False
		FeedsUpdated = False
		StausMsg = ''
		feed_id = False
		try:
			if context.get('channel_id'):
				ChannelID = context['channel_id']
			else:
				ChannelID = self.channel_id
			context['ebay_item_id'] = EbayProdData['ItemID']
			template_data = self.GetOdooTemplateData(EbayProdData, ChannelID)
			if EbayProdData.get('PictureDetails') and EbayProdData['PictureDetails'].get('PictureURL'):
				image_url = EbayProdData['PictureDetails']['PictureURL']
				if isinstance(image_url, (list)):
					image_url = image_url[0]
				photo = base64.encodestring(urllib.request.urlopen(image_url).read())
				template_data.update({'image': photo})
			if EbayProdData.get('Variations'):
				variant_list = self.CreateOdooVariantFeed(EbayProdData,mapping_id)
				if variant_list:
					template_data.update({'feed_variants': variant_list})
			# if EbayProdData.has_key('ShippingDetails') and EbayProdData['ShippingDetails'].has_key('SalesTax'):
			#   tax_id = self._alulateSalesTax(EbayProdData['ShippingDetails']['SalesTax'])
			#   if tax_id:
			#       template_data.update({'taxes_id':[(6, 0, [tax_id])]})
			if not mapping_id:
				feed_id = FeedObj.create(template_data)
				if ChannelID.debug == 'enable':
					_logger.info('------------Template %s created-----',feed_id.name)
				status = True
				FeedsCreated = True
			else:
				res = mapping_id.write(template_data)
				if ChannelID.debug == 'enable':
					_logger.info('------------Template %s Updated-----',mapping_id.name)
				if res:
					FeedsUpdated = True
					mapping_id.state = 'update'
				status = True
				FeedsCreated = False
		except Exception as e:
		  _logger.info('------------Exception-CreateOdooTemplate------%r',e)
		  StausMsg = "Error in Fetching Product: %s" % e
		finally:
			return {
				'status': status,
				'StausMsg': StausMsg,
				'FeedsCreated': FeedsCreated,
				'product_feed_id': feed_id,
				'FeedsUpdated': FeedsUpdated,
				'mapping_id': mapping_id,
			}

	@api.model
	def _CreateAttributeString(self, EbayAttibuteString):
		if EbayAttibuteString['VariationSpecifics']['NameValueList']:
			EbayNameValueList = EbayAttibuteString[
				'VariationSpecifics']['NameValueList']
			AttString = []
			if isinstance(EbayNameValueList, (dict)):
				EbayNameValueList = [EbayNameValueList]
			for EbayValue in EbayNameValueList:
				AttString.append(EbayValue['Value'])
			AttString.sort()
			AttString = ",".join(str(x) for x in AttString)
			return AttString

	@api.model
	def get_product_data_using_product_id(self, item_id, ChannelID):
		api_obj = self.env["multi.channel.sale"]._get_api(ChannelID, 'Trading')
		context = dict(self._context or {})
		context.update({'channel_id': ChannelID})
		res = {}
		StausMsg = ''
		if api_obj['status']:
			try:
				result = []
				callData = {
					'DetailLevel': 'ReturnAll',  # ItemReturnDescription
					'ItemID': item_id,
					'IncludeItemSpecifics': True,
					'IncludeTaxTable': True
				}
				response = api_obj['api'].execute('GetItem', callData)
				result_dict = response.dict()
				if result_dict['Ack'] == 'Success':
					if type(result_dict['Item']) == list:
						result.extend(result_dict['ItemArray']['Item'])
					else:
						result.append(result_dict['Item'])
			except Exception as e:
				StausMsg += 'Error in geting the product from Ebay %s'% str(e)
				_logger.info('----------Exception in get_product_data_using_product_id--------%r',e)
			finally:
				return {'result':result,'StausMsg':StausMsg}

	@api.model
	def get_product_using_product_id(self, item_id, ChannelID):
		create_ids = []
		update_ids = []
		# api_obj = self.env["multi.channel.sale"]._get_api(ChannelID, 'Trading')
		context = dict(self._context or {})
		context.update({'channel_id': ChannelID})
		res = {}
		resp = self.get_product_data_using_product_id(item_id, ChannelID)
		result = resp.get('result')
		try:
			res = self.with_context(context)._CreateOdooFeed(result)
		except Exception as e:
			_logger.info('-------------------%r',e)
			res['StausMsg'] = 'Error in Creating Product Feed %s'%str(e)
		if res.get('mapping_id'):
			update_ids.append(res.get('mapping_id'))
			res['StausMsg'] += 'Product %s have been updated' % res.get('mapping_id').name
		if res.get('product_feed_id'):
			create_ids.append(res.get('product_feed_id'))
		post_res = self.env['channel.operation'].post_feed_import_process(
			ChannelID, {'create_ids': create_ids, 'update_ids': update_ids})
		if res.get('FeedsCreated') and res.get('product_feed_id'):
			res['StausMsg'] += 'Product %s have been imported to odoo' % res.get('product_feed_id').name
		if resp.get('StausMsg'):
			res['StausMsg'] += resp.get('StausMsg')
		return res

	@api.model
	def _CreateOdooFeeds(self, ebay_products):
		context = dict(self._context or {})
		create_ids = []
		update_ids = []
		final_message = ""
		status = True
		res = {}
		if context.get('channel_id'):
			ChannelID = context['channel_id']
		else:
			ChannelID = self.channel_id
		for ebay_product in ebay_products:
			if ebay_product.get('Variations'):
				context['create_product_variant'] = True
			res = self.with_context(context)._CreateOdooFeed(ebay_product)
			final_message += res['StausMsg']
			if res.get('FeedsCreated'):
				create_ids.append(res.get('product_feed_id'))
			if res.get('FeedsUpdated'):
				update_ids.append(res.get('mapping_id'))

		return {'message': final_message,
				'create_ids': create_ids,
				'update_ids': update_ids,
				}

	@api.model
	def _FetchStoreSellerItems(self, api):
		message =  'No Products To Import In This Time Interval..'
		status = True
		result = False
		total = 0
		context = dict(self._context or {})
		from_datetime = context['from_datetime']
		to_datetime = context['to_datetime']
		try:
			page = 1
			result = []
			EntriesPerPage = 1
			while True:
				callData = {
					'DetailLevel': 'ReturnAll',  # ItemReturnDescription
					'Pagination': {'EntriesPerPage': EntriesPerPage, 'PageNumber': page},
					'UserID': context['ebay_sellerid'],
					'IncludeVariations': True,
					'StartTimeFrom': from_datetime,
					'StartTimeTo': to_datetime,
					# 'OutputSelector':self._output_selector,
				}
				if context.get('StoreCategID'):
					callData['CategoryID'] = context['StoreCategID']
				response = api.execute('GetSellerList', callData)
				
				result_dict = response.dict()
				# _logger.info('-----------result_dict-----%r',result_dict)
				if result_dict['Ack'] == 'Success':
					if result_dict['ItemArray']:
						if type(result_dict['ItemArray']['Item']) == list:
							result.extend(result_dict['ItemArray']['Item'])
						else:
							result.append(result_dict['ItemArray']['Item'])
						if result_dict['HasMoreItems'] == 'true':
							page = page + 1
						else:
							break
					else:
						status = False
						message = 'No Products To Import In This Time Interval..'
						break
				else:
					message = message + 'STATUS : %s <br>' % result_dict['Ack']
					message = message + \
						'PAGE : %s <br>' % result_dict['PageNumber']
					message = message + \
						'ErrorCode : %s <br>' % result_dict[
							'Errors']['ErrorCode']
					message = message + \
						'ShortMessage : %s <br>' % result_dict[
							'Errors']['ShortMessage']
					message = message + \
						"LongMessage: %s <br>" % result_dict[
							'Errors']['LongMessage']
					status = False
					break
			total = result_dict['PaginationResult']['TotalNumberOfEntries']
		except Exception as e:
			_logger.info('------------Exception--FetchStoreSellerItems-----%r', e)
			message = "%s" % str(e)
			status = False
		return {'status': status, 'message': message, 'result': result, 'total': total}

	def import_now(self):
		create_ids, update_ids, map_create_ids, map_update_ids = [], [], [], []
		for record in self:
			final_message = ""
			status = True
			context = dict(self._context or {})
			ConfObj = self.env["multi.channel.sale"]
			APIResult = ConfObj._get_api(record.channel_id, 'Trading')
			if APIResult['status']:
				if record.import_using == 'date':
					default_data = ConfObj._get_default_data(record.channel_id)
					if record.store_category_id:
						context[
							'StoreCategID'] = record.store_category_id.store_category_id
					context['from_datetime'] = record.start_time_from
					context['to_datetime'] = record.start_time_to
					context['ebay_sellerid'] = default_data[
						'data']['ebay_sellerid']
					fetch_products = record.with_context(
						context)._FetchStoreSellerItems(APIResult['api'])
					if fetch_products['status']:
						res = self.with_context(context)._CreateOdooFeeds(
							fetch_products['result'])
						post_res = record.env['channel.operation'].post_feed_import_process(
							self.channel_id, {'create_ids': res.get(
								"create_ids"), 'update_ids': res.get('update_ids')})
						create_ids += post_res.get('create_ids')
						update_ids += post_res.get('update_ids')
						map_create_ids += post_res.get('map_create_ids')
						map_update_ids += post_res.get('map_update_ids')
						final_message = res['message']
					else:
						final_message = fetch_products['message']
				else:
					res = record.get_product_using_product_id(record.store_product_id, record.channel_id)
					final_message = res['StausMsg']
			else:
				final_message = APIResult['message']
		final_message += self.env['multi.channel.sale'].get_feed_import_message(
			'product', create_ids, update_ids, map_create_ids, map_update_ids
		)
		return self.env['multi.channel.sale'].display_message(final_message)

	@api.model
	def import_products_by_cron(self):
		"""
		Imports the products through cron. Takes startTimeTo or EndTimeTo from view( depending on filter )
		and calculates the startTimeTo and endTimeto.. Passes the parameters to fetch from ebay in context.
		"""
		context = dict(self._context or {})
		create_date_from = ''
		final_message = ""
		status = True
		start_date_from = ''
		start_date_to = ''
		ChannelIDs = self.env['multi.channel.sale'].search(
			[('channel', '=', 'ebay'), ('active', '=', True),('state','=','validate')])
		for ChannelID in ChannelIDs:
			if ChannelID.debug == 'enable':
				_logger.info('------------------Product Cron started for the Instance ID= %r ---- Time = %r',str(ChannelID.name), str(datetime.now()))
			api_obj = self.env['multi.channel.sale']._get_api(
				ChannelID, 'Trading')
			interval_number = ChannelID.ebay_product_cron_interval_number
			interavl_type = str(ChannelID.ebay_product_cron_interval_type)
			cron_StoreCategID = ChannelID.ebay_product_store_category_id
			start_date_to =  str(datetime.now().replace(microsecond=0))
			if interavl_type == 'minutes':
				start_date_from = datetime.strptime(
					start_date_to, "%Y-%m-%d %H:%M:%S") + relativedelta(minutes=- interval_number)
				start_date_from = start_date_from.strftime("%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'hours':
				start_date_from = datetime.strptime(
					start_date_to, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=- interval_number)
				start_date_from = start_date_from.strftime("%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'days':
				start_date_from = datetime.strptime(
					start_date_to, "%Y-%m-%d %H:%M:%S") + relativedelta(days=- interval_number)
				start_date_from = start_date_from.strftime("%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'months':
				start_date_from = datetime.strptime(
					start_date_to, "%Y-%m-%d %H:%M:%S") + relativedelta(months=- interval_number)
				start_date_from = start_date_from.strftime("%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'weeks':
				start_date_from = datetime.strptime(
					start_date_to, "%Y-%m-%d %H:%M:%S") + relativedelta(weeks=- interval_number)
				start_date_from = start_date_from.strftime("%Y-%m-%d %H:%M:%S")
			if api_obj['status']:
				default_data = self.env[
					'multi.channel.sale']._get_default_data(ChannelID)
				if cron_StoreCategID:
					context['StoreCategID'] = cron_StoreCategID.StoreCategID
				context['from_datetime'] = start_date_from
				context['to_datetime'] = start_date_to
				context['EntriesPerPage'] = 1
				context['ebay_sellerid'] = default_data[
					'data']['ebay_sellerid']
				context['channel_id'] = ChannelID
				fetch_products = self.with_context(
					context)._FetchStoreSellerItems(api_obj['api'])
				if fetch_products['status']:
					try:
						res = self.with_context(context)._CreateOdooFeeds(
							fetch_products['result'])
						post_res = self.env['channel.operation'].post_feed_import_process(
							ChannelID, {'create_ids': res.get(
								"create_ids"), 'update_ids': res.get('update_ids')})
						final_message = res['message']
						if ChannelID.debug == 'enable':
							_logger.info('--------Feed created usign cron--------%r',res)
					except Exception as e:
						_logger.info('--------Exception in fetching Products usign Cron--------%r',e)
				else:
					final_message = 'No Products To Import In This Time Interval..'
			else:
				final_message = api_obj['message']
		
	@api.model
	def _default_channel_id(self):
		return self._context['active_id']

	store_category_id = fields.Many2one(
		comodel_name='channel.category.mappings',
		string='Ebay Category',
		domain="[('category_name','!=',False)]",
		help="Use this option, if you want to import products filtered for any specific category on ebay.")
	detaillevel = fields.Char(
		string='Default Detail Level',
		size=50,
		required=1,
		readonly=1,
		invisible=0,
		default='ReturnAll')
	start_time_from = fields.Datetime(
		string='Start Time From',
		help="Specifies the earliest (oldest) date to use in a date range filter based on item start time.")
	start_time_to = fields.Datetime(
		string='Start Time To',
		help="Specifies the latest (most recent) date to use in a date range filter based on item start time.")
	channel_id = fields.Many2one(
		comodel_name='multi.channel.sale',
		string='Channel ID',
		required=1, readonly=1,
		default=_default_channel_id,
		help="Channel id which you want to use for importing the ebay categories")
	import_using = fields.Selection(
		[('date','Start Time'),('prod_id','Ebay Item ID')],
		string='Import Using',
		required=1,
		default='date',
		help="How do you want to import Products")
	store_product_id = fields.Char(
		string="Item Id",
		help="ID of the product you want ot import"
	)