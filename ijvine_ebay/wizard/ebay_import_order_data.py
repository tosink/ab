# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import api, fields, models, _
from odoo import tools, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from ..ebaysdk.trading import Connection as Trading
def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.

	try:

		text =  unquote_plus(text.encode('utf8'))
		return text
	except Exception as e:
		return text

class ImportEbayOrders(models.TransientModel):
	_name = "import.ebay.orders"
	_description = "Import Ebay Orders"
	_output_selector = "HasMoreOrders,PageNumber,PaginationResult,PaginationResult.TotalNumberOfEntries,OrderArray,OrderArray.Order"
	product_created = 0

	@api.model
	def _create_country(self, CountryName, CountryCode):
		country_obj = self.env['res.country']
		exists = country_obj.search([('name', '=', CountryName)])
		if exists:
			country_id = exists[0].id
		else:
			country_id = country_obj.create(
				{'name': CountryName, 'code': CountryCode}).id
		return country_id

	@api.model
	def _FillOdooPartnerDetails(self, ebay_order):
		""" Creates a partner with all the necessary fields and return a partner object"""
		vals = {}
		status = True
		status_message = 'Pertner feed created successfully!!!'
		context = dict(self._context or {})
		if context.get('channel_id'):
			ChannelID = context['channel_id']
		else:
			ChannelID = self.channel_id
		EbayCustomerInfo = ebay_order[
			'TransactionArray']['Transaction'][0]['Buyer']
		ebay_cust_shipping_adrs = ebay_order['ShippingAddress']
		vals['store_id'] = ebay_order['BuyerUserID']
		vals['channel_id'] = ChannelID.id
		vals['channel'] = 'ebay'
		name = ''
		if EbayCustomerInfo.get('UserFirstName'):
			name = EbayCustomerInfo.get('UserFirstName')
		if name == '':
			if ebay_cust_shipping_adrs.get('Name'):
				name = ebay_cust_shipping_adrs.get('Name')
			else:
				name = 'No Name'
		vals['name'] = name
		# vals['last_name'] = EbayCustomerInfo.get('UserLastName')
		if EbayCustomerInfo.get('Email') and EbayCustomerInfo.get('Email') != 'Invalid Request':
			vals['email'] = EbayCustomerInfo.get('Email') 
		vals['street'] = ebay_cust_shipping_adrs.get('Street1')
		vals['street2'] = ebay_cust_shipping_adrs.get('Street2')
		if ebay_cust_shipping_adrs.get('Phone') and ebay_cust_shipping_adrs.get('Phone') != 'Invalid Request':
			vals['phone'] = ebay_cust_shipping_adrs.get('Phone')
		vals['city'] = ebay_cust_shipping_adrs.get('CityName')
		vals['zip'] =  ebay_cust_shipping_adrs.get('PostalCode')
		vals['state_id'] = ebay_cust_shipping_adrs.get('StateOrProvince')
		vals['country_id'] = ebay_cust_shipping_adrs.get('Country')
		return vals
	@api.model
	def CreateShippingInvoiceAddress(self, ebay_order):
		""" Creates shipping address and invoice address and returns dixtionary of these address values"""
		vals = {}
		EbayCustomerInfo = ebay_order[
			'TransactionArray']['Transaction'][0]['Buyer']
		ebay_cust_shipping_adrs = ebay_order['ShippingAddress']
		vals['invoice_partner_id'] = ebay_order['BuyerUserID']
		name = ''
		if EbayCustomerInfo.get('UserFirstName'):
			name = EbayCustomerInfo.get('UserFirstName')
		if name == '':
			if ebay_cust_shipping_adrs.get('Name'):
				name = ebay_cust_shipping_adrs.get('Name')
			else:
				name = 'No Name'
		# vals['last_name'] = EbayCustomerInfo.get('UserLastName')
		vals['customer_name'] = name
		vals['invoice_name'] = name
		if EbayCustomerInfo.get('Email') and EbayCustomerInfo.get('Email')!= 'Invalid Request':
			vals['customer_email'] = EbayCustomerInfo.get('Email')
			vals['invoice_email'] = EbayCustomerInfo.get('Email')
		else:
			vals['customer_email'] = 'No Email'
			vals['invoice_email'] = 'No Email'
		vals['invoice_street'] = ebay_cust_shipping_adrs.get('Street1')
		vals['invoice_street2'] = ebay_cust_shipping_adrs.get('Street2')
		if ebay_cust_shipping_adrs.get('Phone') and ebay_cust_shipping_adrs.get('Phone') != 'Invalid Request':
			vals['invoice_phone'] = ebay_cust_shipping_adrs.get('Phone')
		vals['invoice_city'] = ebay_cust_shipping_adrs.get('CityName')
		vals['invoice_zip'] = ebay_cust_shipping_adrs.get('PostalCode')
		vals['invoice_state_id'] = ebay_cust_shipping_adrs.get('StateOrProvince')
		vals['invoice_country_id'] = ebay_cust_shipping_adrs.get('Country')
		return vals

	@api.model
	def _CreateOdooPartnerFeed(self, EbayOrder):
		context = dict(self._context or {})
		MapObj = self.env['channel.partner.mappings']
		FeedPartnerEnv = self.env['partner.feed']
		# MapExists =
		# MapObj.search([('store_customer_id','=',EbayOrder['BuyerUserID'])])
		vals = {}
		# if MapExists:
		# 	OdooPartnerId = MapExists[0].odoo_partner.id
		# else:
		FeedExists = FeedPartnerEnv.search(
			[('store_id', '=', EbayOrder.get('BuyerUserID'))], limit=1)
		vals = self._FillOdooPartnerDetails(EbayOrder)
		if FeedExists:
			FeedExists.write(vals)
			FeedObj = FeedExists
			FeedExists.state = 'update'
		else:
			FeedObj = FeedPartnerEnv.create(vals)
			# res = FeedObj.import_item()
		return FeedObj.store_id

	@api.model
	def _CreateOrderFeedLine(self, product_obj, odoo_order_id, odoo_partner_id, ebay_order):
		sale_order_line_id = 0
		try:
			if product_obj:
				ebay_items = ebay_order['TransactionArray']['Transaction']
				description_sale = product_obj.description_sale
				if not product_obj.description_sale:
					description_sale = product_obj.name
				order_line_data = {
					'product_id': product_obj.id,
					'name': description_sale,
					'product_uom_qty': ebay_items[0]['QuantityPurchased'],
					'price_unit': product_obj.lst_price,
					'order_id': odoo_order_id,
					'product_uom': product_obj.uom_id.id,
				}
				ijvine_tax_ids = []
				for ijvine_tax_id in product_obj.taxes_id:
					ijvine_tax_ids.append(ijvine_tax_id.id)
				if ijvine_tax_ids:
					order_line_data.update({'tax_id': [(6, 0, ijvine_tax_ids)]})
				sale_order_line_id = self.env[
					'sale.order.line'].create(order_line_data).id
		except Exception as e:
			_logger.info(
				'---------Exception in CreateOdooOrderLine-----------%r', e)
		finally:
			return sale_order_line_id

	@api.model
	def _CreateAttributeString(self, EbayAttibuteString):
		if EbayAttibuteString['VariationSpecifics']['NameValueList']:
			EbayNameValueList = EbayAttibuteString[
				'VariationSpecifics']['NameValueList']
			AttString = []
			if isinstance(EbayNameValueList, (dict)):
				EbayNameValueList = [EbayNameValueList]
			for EbayValue in EbayNameValueList:
				AttString.append(_unescape(EbayValue['Value']))
			AttString.sort()
			AttString = ",".join(str(x) for x in AttString)
			return AttString

	@api.model
	def _CheckIfProductExists(self, ebay_item):
		MapExists = []
		ProdMapobj = self.env['channel.product.mappings']
		if ebay_item.get('Variation'):
			attr_string = self._CreateAttributeString(ebay_item['Variation'])
			MapExists = ProdMapobj.search([('store_product_id', '=', ebay_item['Item'][
				'ItemID']), ('store_variant_id', '=', attr_string)])
		else:
			MapExists = ProdMapobj.search([('store_product_id', '=', ebay_item['Item'][
				'ItemID']), ('store_variant_id', '=', 'No Variants')])
		return MapExists

	def get_default_payment_method(self, journal_id):
		""" @params journal_id: Journal Id for making payment
						@params context : Must have key 'ecommerce' and then return payment  method based on Odoo Bridge used else return the default payment method for Journal
						@return: Payment method ID(integer)"""

		payment_method_ids = self.env['account.journal'].browse(
			journal_id)._default_inbound_payment_methods()
		if payment_method_ids:
			return payment_method_ids[0].id
		return False

	@api.model
	def _GetFeedOrderProduct(self, ebay_item, channel_id):
		status_message = 'Order Lines Successfully Created'
		status = True
		product_obj = 0
		msg = ''
		res = {}
		product_map_id = False
		ProductFeedExists = False
		if isinstance(ebay_item, (list)):
			ebay_item = ebay_item[0]
		try:
			map_exists = self._CheckIfProductExists(ebay_item)
			if not map_exists:
				res = self.env['import.ebay.products'].get_product_using_product_id(
					ebay_item['Item']['ItemID'], channel_id)
				product_feed_exists = self.env['product.feed'].search(
					[('store_id', '=', ebay_item['Item']['ItemID'])])
				if product_feed_exists:
					ProductFeedExists = True
				product_map_id = self._CheckIfProductExists(ebay_item)
				
			else:
				product_map_id = map_exists
			res['product_map_id'] = product_map_id
			res['ProductFeedExists'] = ProductFeedExists
		except Exception as e:
			_logger.info('--------------Exception--%r',e)
			res['StausMsg'] += '%s' % str(e.message)
			status = False
		finally:
			return res

	
	@api.model
	def GetVariantID(self, ebay_item):
		variant_id = 'No Variants'
		if ebay_item.get('Variation'):
			variant_id = self._CreateAttributeString(ebay_item['Variation'])
		return variant_id

	@api.model
	def GetFeedOrderProductValues(self,ebay_item=False, ChannelID=False):
		feed_vals = {}
		feed_vals.update({
				'line_price_unit': ebay_item['TransactionPrice']['value'],
				'line_product_uom_qty': ebay_item['QuantityPurchased'],
				'line_product_id': ebay_item['Item']['ItemID'],
				'line_variant_ids':self.GetVariantID(ebay_item)
			})
		res = self._GetFeedOrderProduct(ebay_item, ChannelID)
		if res.get('mapping_id'):
			feed_vals.update({'line_name':  res.get('mapping_id').name})
		if res.get('product_feed_id'):
			feed_vals.update({'line_name':  res.get('product_feed_id').name})
		if res.get('product_map_id'):
			feed_vals.update({
				'line_name': res['product_map_id'].product_name.name,
				'line_variant_ids': res['product_map_id'].store_variant_id
			})
		return {'feed_vals': feed_vals, 'product_res':res}

	@api.model
	def CreateFeedOrderLines(self, ebay_order=False, ChannelID=False, OrderFeed=False):
		feed_vals = {}
		ProductFeedExisted = False
		ProductFeedCreated = False
		ebay_items = ebay_order['TransactionArray']['Transaction']
		shipping = ebay_order.get('ShippingServiceSelected')
		# shipping_cost = 
		if len(ebay_items) <= 1 and not shipping:
			if isinstance(ebay_items, (list)):
				ebay_item = ebay_items[0]
			res = self.GetFeedOrderProductValues(ebay_item, ChannelID)
			feed_vals.update(res.get('feed_vals'))
			
		else:
			feed_vals.update({'line_type': 'multi'})
			line_vals_list = []
			for ebay_item in ebay_items:
				line_vals = {}
				res = self.GetFeedOrderProductValues(ebay_item, ChannelID)
				line_vals.update(res.get('feed_vals'))
				if not OrderFeed:
					line_vals_list.append((0, 0, line_vals))
				else:
					variant_id = self.GetVariantID(ebay_item)
					order_line_exists = OrderFeed.line_ids.search([('line_product_id','=',ebay_item['Item']['ItemID']),('line_variant_ids','=',variant_id)], limit=1)
					if order_line_exists:
						line_vals_list.append((1, order_line_exists.id, line_vals))
					else:
						line_vals_list.append((0, 0, line_vals))
			feed_vals.update({'line_ids': line_vals_list})
		if res.get('product_res').get('product_feed_id'):
			ProductFeedCreated = True
		if res.get('product_res').get('ProductFeedExists'):
			ProductFeedExisted = True
		return {'feed_vals': feed_vals, 'ProductFeedExisted': ProductFeedExisted, 'ProductFeedCreated': ProductFeedCreated}

	@api.model
	def _CreateOrderFeed(self, ebay_order, odoo_feed_id):
		status = True
		message = ''
		CreatedFeed = False
		ProductFeedCreated = False
		OrderFeedCreated = False
		ProductFeedExisted = False
		OrderFeedUpdated = False
		order_feed_id = False
		context = dict(self._context or {})
		feed_obj = self.env['order.feed']
		res = {}
		feed_exists = feed_obj.search([('store_id', '=', ebay_order['OrderID'])], limit=1)
		if context.get('channel_id'):
			ChannelID = context['channel_id']
		else:
			ChannelID = self.channel_id
		if odoo_feed_id:
			feed_vals = {
				'partner_id': odoo_feed_id,
				'channel_id': ChannelID.id,
				'payment_method': ebay_order['CheckoutStatus']['PaymentMethod'],
				'name': ebay_order['OrderID'],
				'store_id': ebay_order['OrderID'],
				'order_state': ebay_order['OrderStatus'],
				'line_source':'product',
				'currency': ebay_order.get('TransactionArray').get('Transaction')[0].get('TransactionPrice').get('_currencyID'),
			}
			shiping_res = self.CreateShippingInvoiceAddress(ebay_order)
			feed_vals.update(shiping_res)
			if ebay_order.get('ShippingServiceSelected'):
				shipping_service = ebay_order.get('ShippingServiceSelected')
				feed_vals['carrier_id'] = shipping_service.get(
					'ShippingService')
			res = self.CreateFeedOrderLines(ebay_order, ChannelID, feed_exists)
			feed_vals.update(res.get('feed_vals'))
			ProductFeedCreated = res.get('ProductFeedCreated')
			ProductFeedExisted = res.get('ProductFeedExisted')
			if not feed_exists:
				order_feed_id = ChannelID._create_feed(feed_obj, feed_vals)
				OrderFeedCreated = True
			else:
				order_feed_id = feed_exists
				feed_exists.write(feed_vals)
				feed_exists.state = 'update'
				OrderFeedUpdated = True
			shipping = ebay_order.get('ShippingServiceSelected')
			if shipping and float(shipping.get('ShippingServiceCost').get('value')) > 0.0:
				
				self.create_delivery_line(shipping, order_feed_id.id)

		return {
			'status': status,
			'message': message,
			'ProductFeedCreated': ProductFeedCreated,
			'OrderFeedCreated': OrderFeedCreated,
			'ProductFeedExisted': ProductFeedExisted,
			'OrderFeedUpdated': OrderFeedUpdated,
			'order_feed_id': order_feed_id
		}

	@api.model
	def create_delivery_line(self, data, order_feed_id, tax=False):
		taxArray = []
		orderLineFeedModel = self.env['order.line.feed']
		try:
			# if tax:
			# 	for value in tax.values():
			# 		tax_ship_itmes=value.get('applies').get('items').get('S')
			# 		if tax_ship_itmes:
			# 			taxDict = dict(
			# 					rate=value.get('rate_value'),
			# 					name=value.get('description'),
			# 					)
			# 			include_in_price=value.get('price_includes_tax')
			# 			tax_rate_type=value.get('rate_type')
			# 			if include_in_price == 'Y':
			# 				include_in_price=True
			# 			else:
			# 				include_in_price=False
			# 			if tax_rate_type == 'P':
			# 				tax_rate_type='percent'
			# 			else:
			# 				tax_rate_type='fixed'

			# 			taxDict.update(
			# 				include_in_price=include_in_price,
			# 				tax_type=tax_rate_type
			# 				)
			# 			taxArray.append(taxDict)
			delivery_vals = dict(
				line_name='Delivery',
				line_price_unit=data.get('ShippingServiceCost').get('value'),
				line_product_id=data.get('ShippingService'),
				line_source='delivery',
				line_taxes=taxArray,
				line_product_uom_qty=1,
				order_feed_id=order_feed_id,
				)
			existOrderLine = orderLineFeedModel.search(
				[('order_feed_id', '=', order_feed_id),
				('line_product_id', '=', data.get('ShippingService')),
				('line_source', '=', 'delivery')]
				)
			if existOrderLine:
				existOrderLine.write(delivery_vals)
			else:
				orderLineFeedModel.create(delivery_vals)
		except Exception as e:
			_logger.info('----------Exception in Creating Shipping Method----------%r',str(e.message))
		

	@api.model
	def _CreateOdooFeeds(self, EbayOrders):
		context = dict(self._context or {})
		message = ""
		status = True
		ProductFeedsCreated = 0
		message = ''
		CreatedOrderFeeds = 0
		ProductFeedExisted = 0
		OrderFeedUpdated = 0
		create_ids = []
		update_ids = []
		result = {}
		if context.get('channel_id'):
			ChannelID = context['channel_id']
		else:
			ChannelID = self.channel_id
		try:
			for EbayOrder in EbayOrders:
				if EbayOrder.get('TransactionArray').get('Transaction'):
					store_id = EbayOrder.get('TransactionArray').get(
						'Transaction')[0].get('Item').get('ItemID')
					if ChannelID.debug == 'enable':
						_logger.info('--------Ebay Created  Order Date-----------%r',EbayOrder.get('TransactionArray').get(
						'Transaction')[0].get('CreatedDate'))
				partner_feed_id = self.with_context(
					context)._CreateOdooPartnerFeed(EbayOrder)
				result = self.with_context(context)._CreateOrderFeed(
					EbayOrder, partner_feed_id)
				if result['ProductFeedCreated']:
					ProductFeedsCreated += 1
				if result['OrderFeedCreated']:
					create_ids.append(result.get('order_feed_id'))
					CreatedOrderFeeds += 1
				if result['ProductFeedExisted']:
					ProductFeedExisted += 1
				if result['OrderFeedUpdated']:
					update_ids.append(result.get('order_feed_id'))
					OrderFeedUpdated += 1
				message += result['message']
			if not ChannelID.auto_evaluate_feed:
				if CreatedOrderFeeds > 0:
					message += '%s Orders have been successfully imported to odoo.<br/>' % CreatedOrderFeeds
				if ProductFeedsCreated > 0:
					message += '%s new product feeds have been created please update the product feed.<br/>' % ProductFeedsCreated
				if ProductFeedExisted > 0:
					message += '%s product feeds have not been evaluated yet, please evaluate the feeds before importing the orders<br/>' % ProductFeedExisted
				if OrderFeedUpdated > 0:
					message += '%s product feeds have been updated<br/>' % OrderFeedUpdated
			if CreatedOrderFeeds == 0 and ProductFeedsCreated == 0 and ProductFeedExisted == 0 and OrderFeedUpdated == 0:
				message += 'Nothing to import, All orders have been imported already!!!<br/>'

		except Exception as e:
			_logger.info(
				'-------Exception in CreateOdooOrders--------------%r', e)
		finally:
			return {'message': message,
					'create_ids': create_ids,
					'update_ids': update_ids}

	@api.model
	def _FetchEbayOrders(self, api):
		message = ""
		status = True
		result = False
		total = 0
		callData = {}
		context = dict(self._context or {})
		try:
			page = 1
			result = []
			EntriesPerPage = 1
			while True:
				if context.get('order_id'):
					callData.update({
						'OrderIDArray': {'OrderID': str(context.get('order_id'))},
						'OrderRole': 'Seller'
					})
				callData.update({
					'DetailLevel': 'ReturnAll',  # ItemReturnDescription
					'Pagination': {'EntriesPerPage': EntriesPerPage, 'PageNumber': page},
					'CreateTimeFrom': context['from_datetime'],
					'CreateTimeTo':  context['to_datetime'],
					# 'OutputSelector': self._output_selector,
					'SortingOrder':'Ascending',
				})
				if context.get('order_status'):
					callData['OrderStatus'] = context['order_status']
				response = api.execute('GetOrders', callData)
				result_dict = response.dict()
				if self.channel_id.debug == 'enable':
					_logger.info('-------Response---------- %r',result_dict)
				if result_dict.get('Ack') == 'Success':
					if not result_dict['OrderArray']:
						message = 'No Orders To Import In This Time Interval..'
					elif result_dict['OrderArray'] and result_dict['OrderArray']['Order'] and type(result_dict['OrderArray']['Order']) == list:
						result.extend(result_dict['OrderArray']['Order'])
					else:
						result.append(result_dict['OrderArray']['Order'])
					if result_dict['HasMoreOrders'] == 'true':
						page = page + 1
					else:
						break
				else:
					message = message + 'STATUS : %s <br>' % result_dict['Ack']
					message = message + \
						'PAGE : %s <br>' % result_dict['PageNumber']
					message = message + \
						'ErrorCode : %s <br>' % result_dict[
							'Errors']['ErrorCode']
					message = message + \
						'ErrorParameters : %s <br>' % result_dict[
							'Errors']['ErrorParameters']
					message = message + \
						"LongMessage: %s <br>" % result_dict[
							'Errors']['LongMessage']
					status = False
					break
			total = result_dict['PaginationResult']['TotalNumberOfEntries']
		except Exception as e:
			message = "Error in Fetching Orders: %s" % e
			_logger.info(
				'--------Exception in _FetchEbayOrders-------------%r', e)
			status = False
		return {'status': status, 'message': message, 'result': result, 'total': total}

	def import_now(self):
		create_ids, update_ids, map_create_ids, map_update_ids = [], [], [], []
		for record in self:
			final_message = ""
			status = True
			context = dict(self._context or {})
			ConfObj = self.env["multi.channel.sale"]
			api_obj = ConfObj._get_api(record.channel_id, 'Trading')
			if api_obj['status']:
				default_data = ConfObj._get_default_data(record.channel_id)
				# context['sort_order'] = default_data[
				#     'data']['ebay_sorting_order']
				context['order_status'] = record.ebay_order_status
				context['ebay_sellerid'] = default_data[
					'data']['ebay_sellerid']
				context['from_datetime'] = record.create_time_from
				context['to_datetime'] = record.create_time_to
				context['order_id'] = record.ebay_order_id
				EbayOrders = record.with_context(
					context)._FetchEbayOrders(api_obj['api'])
				if EbayOrders['status']:
					res = record.with_context(
						context)._CreateOdooFeeds(EbayOrders['result'])
					post_res = record.env['channel.operation'].post_feed_import_process(
						self.channel_id, {'create_ids': res.get(
							"create_ids"), 'update_ids': res.get('update_ids')})
					create_ids += post_res.get('create_ids')
					update_ids += post_res.get('update_ids')
					map_create_ids += post_res.get('map_create_ids')
					map_update_ids += post_res.get('map_update_ids')
					final_message = res['message']
				else:
					final_message = 'No Orders To Import In This Time Interval..'
			else:
				final_message = api_obj['message']
		final_message += self.env['multi.channel.sale'].get_feed_import_message(
			'order', create_ids, update_ids, map_create_ids, map_update_ids
		)
		return self.env['multi.channel.sale'].display_message(final_message)

	@api.model
	def import_orders_by_cron(self):
		"""
		Imports the orders through cron. Takes startTimeTo from view
		and calculates the startTimeTo .. Stores the parameters to fetch from ebay in context.
		"""
		create_date_from = ''
		final_message = ""
		status = True
		context = dict(self._context or {})
		ChannelIDs = self.env['multi.channel.sale'].search(
			[('channel', '=', 'ebay'), ('active', '=', True),('state','=','validate')])
		for ChannelID in ChannelIDs:
			if ChannelID.debug == 'enable':
				_logger.info('------------------Order Cron started for the Instance ID= %r ---- Time = %r',str(ChannelID.name), str(datetime.now()))
			api_obj = self.env['multi.channel.sale']._get_api(
				ChannelID, 'Trading')
			interval_number = ChannelID.ebay_order_cron_interval_number
			interavl_type = str(ChannelID.ebay_order_cron_interval_type)
			nextcall = str(datetime.now().replace(microsecond=0))
			if interavl_type == 'minutes':
				create_date_from = datetime.strptime(
					nextcall, "%Y-%m-%d %H:%M:%S") + relativedelta(minutes=- interval_number)
				create_date_from = create_date_from.strftime(
					"%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'hours':
				create_date_from = datetime.strptime(
					nextcall, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=- interval_number)
				create_date_from = create_date_from.strftime(
					"%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'days':
				create_date_from = datetime.strptime(
					nextcall, "%Y-%m-%d %H:%M:%S") + relativedelta(days=- interval_number)
				create_date_from = create_date_from.strftime(
					"%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'months':
				create_date_from = datetime.strptime(
					nextcall, "%Y-%m-%d %H:%M:%S") + relativedelta(months=- interval_number)
				create_date_from = create_date_from.strftime(
					"%Y-%m-%d %H:%M:%S")
			elif interavl_type == 'weeks':
				create_date_from = datetime.strptime(
					nextcall, "%Y-%m-%d %H:%M:%S") + relativedelta(weeks=- interval_number)
				create_date_from = create_date_from.strftime(
					"%Y-%m-%d %H:%M:%S")
			if ChannelID.debug == 'enable':
				_logger.info('-------Date From =====  %r Date To =======  %r---',create_date_from, nextcall)
			if api_obj['status']:
				default_data = self.env[
					'multi.channel.sale']._get_default_data(ChannelID)
				context.update({
					# 'sort_order': default_data['data']['ebay_sorting_order'],
					'order_status': str(ChannelID.ebay_order_status),
					'EntriesPerPage': 1,
					'ebay_sellerid': default_data['data']['ebay_sellerid'],
					'from_datetime': create_date_from,
					'to_datetime': nextcall,
					'channel_id': ChannelID,
				})
				fetch_orders = self.with_context(
					context)._FetchEbayOrders(api_obj['api'])
				if ChannelID.debug == 'enable':
					_logger.info('-----ebay Orders--------%r',fetch_orders)
					
				if fetch_orders['status']:
					try:
						res = self.with_context(
							context)._CreateOdooFeeds(fetch_orders['result'])
						post_res = self.env['channel.operation'].post_feed_import_process(
						ChannelID, {'create_ids': res.get(
							"create_ids"), 'update_ids': res.get('update_ids')})
						if ChannelID.debug == 'enable':
							_logger.info('-----Order feed created using Cron--------%r',res)
					except Exception as e:
						 _logger.info('-----Exception in fetching orders using cron-----------%r',e.message)

				else:
					final_message = 'No Orders To Import In This Time Interval..'

	@api.model
	def _default_channel_id(self):
		return self._context['active_id']

	create_time_from = fields.Datetime(
		string='Create Time From',
		required=True,
		help="The Date from which the orders can be retrieved")
	create_time_to = fields.Datetime(
		string='Create Time To',
		required=True,
		help="The Date upto which the orders can be retrieved.")
	ebay_order_id = fields.Char(
		string='Import by Order Id',
		help="an optional field by which we can import only one order")
	channel_id = fields.Many2one(
		comodel_name='multi.channel.sale',
		string='Channel ID',
		required=True,
		readonly=1,
		default=_default_channel_id)
	# ebay_sorting_order = fields.Selection(
	#     [('Ascending', 'Ascending'), ('Descending', 'Descending')],
	#     string='Sort By',
	#     default="Ascending",
	#     help="sorting order of the returned orders")
	ebay_order_status = fields.Selection(
		[('Active', 'Active'), ('Completed', 'Completed'), ('Canceled', 'Canceled')],
		string='Ebay Order Status',
		default="Completed",
		help="The field is used to retrieve orders that are in a specific state.")