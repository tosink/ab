# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import api, fields, models, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from ..ebaysdk.trading import Connection as Trading


class ImportEbayShippingMethods(models.TransientModel):
    _name = "import.ebay.shipping.methods"
    _description = "Import Ebay Shipping Methods"
    @api.model
    def _CreateOdooShippingFeeds(self, shipping_methods, ChannelID):
        status = True
        message = ''
        ShippingFeedsCreated = False
        ShippingFeedsUpdated = False
        create_ids, update_ids = [], []
        context = dict(self._context or {})
        try:
            for shipping_method in shipping_methods:
                if isinstance(shipping_method, (dict)):
                    shipping_method = [shipping_method]
                shipping_method = shipping_method[0]
                if shipping_method.get('ShippingService') and shipping_method.get('ValidForSellingFlow', 'true'):
                    exists = self.env['shipping.feed'].search(
                        [('name', '=', shipping_method['ShippingService'])], limit=1)
                    values = {
                        'channel_id': ChannelID.id,
                        'channel': 'ebay',
                        'name': shipping_method['ShippingService']
                    }
                    if shipping_method.get('ShippingServiceID'):
                        values.update(
                            {'store_id': shipping_method['ShippingServiceID']})
                    if shipping_method.get('InternationalService'):
                        values.update({'is_international': True})
                    else:
                        values.update({'is_international': False})
                    if shipping_method.get('ShippingCarrier'):
                        values.update(
                            {'shipping_carrier': shipping_method['ShippingCarrier'][0]})
                    else:
                        values.update({'shipping_carrier': 'Other'})
                    if not exists:
                        feed_id = self.env['shipping.feed'].create(values)
                        if ChannelID.debug == 'enable':
                            _logger.info('-------Shipping Feed Created Id = %s-----',values.get('store_id'))
                        create_ids.append(feed_id)
                        ShippingFeedsCreated = True
                    else:
                        res = exists.write(values)
                        if res:
                            if ChannelID.debug == 'enable':
                                _logger.info('---Shipping Feed  Updated ID = %r -----',values.get('store_id'))
                            exists.state = 'update'
                            update_ids.append(exists)
                            ShippingFeedsUpdated = True
            if not ShippingFeedsUpdated or not ShippingFeedsCreated:
                message += 'Nothing to import all shipping methods have been already imported!!'
        except Exception as e:
            _logger.info('-------execption-----%s' % e)
            message = "Error in Fetching Shipping Methods: %s" % e
        finally:
            return {'message': message,
                    'update_ids': update_ids,
                    'create_ids': create_ids
                    }

    @api.model
    def _FetchEbayShippingDetails(self, api):
        message = ""
        status = True
        result = False
        total = 0
        context = dict(self._context or {})
        try:
            result = []
            # 'DetailName' => 'ShippingServiceDetails', 'Version' => 891, 'DetailLevel' => 'ReturnAll'
            callData = {
                'DetailName': 'ShippingServiceDetails',
                'Version': 891
                # 'OutputSelector':self._output_selector,
            }
            response = api.execute('GeteBayDetails', callData)
            result_dict = response.dict()
            if result_dict['Ack'] == 'Success':
                result = result_dict['ShippingServiceDetails']
                if type(result_dict) == list:
                    result.extend(result_dict['ShippingServiceDetails'])
                else:
                    result.append(result_dict['ShippingServiceDetails'])
            else:
                message = message + 'STATUS : %s <br>' % result_dict['Ack']
                message = message + \
                    'ErrorCode : %s <br>' % result_dict['Errors']['ErrorCode']
                message = message + \
                    'ShortMessage : %s <br>' % result_dict[
                        'Errors']['ShortMessage']
                message = message + \
                    "LongMessage: %s <br>" % result_dict[
                        'Errors']['LongMessage']
                status = False
        except Exception as e:
            message = "Error in Fetching Shipping Methods: %s" % e
            status = False
        return {'status': status, 'message': message, 'result': result}

    def import_now(self, ChannelID):
        create_ids, update_ids, map_create_ids, map_update_ids = [], [], [], []
        final_message = ""
        status = True
        context = dict(self._context or {})
        api_obj = self.env["multi.channel.sale"]._get_api(ChannelID, 'Trading')
        if api_obj['status']:
            shipping_methods = self.with_context(
                context)._FetchEbayShippingDetails(api_obj['api'])
            if shipping_methods['status']:
                res = self.with_context(context)._CreateOdooShippingFeeds(
                    shipping_methods['result'], ChannelID)
                if ChannelID.debug == 'enable':
                    _logger.info('------shipping feed created----------%r',res)
                post_res = self.env['channel.operation'].post_feed_import_process(
                    ChannelID, {'create_ids': res.get('create_ids'), 'update_ids': res.get('update_ids')})
                final_message += res.get('message')
                create_ids += post_res.get('create_ids')
                update_ids += post_res.get('update_ids')
                map_create_ids += post_res.get('map_create_ids')
                map_update_ids += post_res.get('map_update_ids')
        final_message += self.env['multi.channel.sale'].get_feed_import_message(
            'shipping methods', create_ids, update_ids, map_create_ids, map_update_ids)
        return final_message
