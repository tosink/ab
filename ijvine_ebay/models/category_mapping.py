# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import tools, api
from odoo import fields, models
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
def _unescape(text):
	##
	# Replaces all encoded characters by urlib with plain utf8 string.
	#
	# @param text source text.
	# @return The plain text.

	try:
		return unquote_plus(text.encode('utf8'))
	except Exception as e:
		return text

class ChannelCategoryMappings(models.Model):

	_inherit = "channel.category.mappings"

	ebay_category_specifics = fields.Text(string="Specifics")
	ebay_category_specifics_values = fields.Text(string="Specific Values")
	ebay_max_names = fields.Integer(
		string="Item Specifics Names",
		default=30,
		help="Maxium number of item specifics to be imported. Default value is 30."
	)
	ebay_max_values_per_name = fields.Integer(
		string="Item Specific Values",
		default=25,
		help="Maxium number of values to be imported for each item Specifics.Default value is 25."
	)

	def getCategorySpecifics(self):
		res = self.getCategorySpecificsapiCall()
		self.ebay_category_specifics = res.get('name_value_list')
		self.ebay_category_specifics_values = res.get('all_value_lists')
		return self.env['multi.channel.sale'].display_message(res.get('message'))


	@api.model
	def getCategorySpecificsapiCall(self, category_id=False, channel_id = False, temp_id = False):
		try:
			message = ""
			storeCateg = self.store_category_id
			channelId =  self.channel_id

			name_value_list = []
			all_value_lists = ""
			if category_id:
				storeCateg = category_id.store_category_id
			if channel_id:
				channelId = channel_id
			api_obj = self.env["multi.channel.sale"]._get_api(channelId, 'Trading')
			api = api_obj['api']
			callData = {
				'DetailLevel': 'ReturnAll',
				'CategorySpecific':{'CategoryID': storeCateg}
			}
			if (temp_id and temp_id.ebay_max_names):
				callData.update({'MaxNames':int(temp_id.ebay_max_names)})
			if  self.ebay_max_names:
				callData.update({'MaxNames':int(self.ebay_max_names)})
			if (temp_id and temp_id.ebay_max_values_per_name):
				callData.update({'MaxValuesPerName':int(temp_id.ebay_max_values_per_name)})
			if self.ebay_max_values_per_name:
				callData.update({'MaxValuesPerName':int(self.ebay_max_values_per_name)})
			response = api.execute('GetCategorySpecifics', callData)
			result_dict = response.dict()
			if result_dict['Ack'] == 'Success':
				if result_dict.get('Recommendations') and result_dict.get('Recommendations').get('NameRecommendation'):
					for specifics in result_dict.get('Recommendations').get('NameRecommendation'):
						recomendations = specifics.get('ValueRecommendation')
						if isinstance(recomendations, (dict)):
							recomendations = [recomendations]
						if recomendations:
							name_value_list.append({'Name':_unescape(specifics.get('Name')),'Value':_unescape(recomendations[0].get('Value'))})
							values = []
							for recom in recomendations:
								values.append(_unescape(recom.get('Value')))
							all_value_lists += "<b><u> %s </u> &nbsp;::</b>  &nbsp;  &nbsp;<b>Available Values </b>   =   %s </br></br>"%(_unescape(specifics.get('Name')), values)
					result_dict = result_dict.get('Recommendations').get('NameRecommendation')
				message = "Specifics related category/product added."
				if not name_value_list:
					message="No eBay specifics found for this category."

			else:
				message = result_dict
		except Exception as e:
			message = "Error in Fetching Category Details: %s" % e

		return {'message':message,'name_value_list':name_value_list,'all_value_lists':all_value_lists}