# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class EbayImportBusinessPolicies(models.TransientModel):
    _name = "ebay.import.business.policies"
    _description = "Import Ebay Business Poilicies"

    @api.model
    def _FetchEbayBusinessPolicies(self, api, ChannelID):
        message = ""
        status = True
        result = []
        try:
            callData = {
                'ShowSellerProfilePreferences': True,
            }
            response = api.execute('GetUserPreferences', callData)
            result_dict = response.dict()
            if ChannelID.debug == 'enable':
                _logger.info('----------Result Dictionary-----------%r',result_dict)
            if result_dict['Ack'] == 'Success':
                if result_dict.get('SellerProfilePreferences'):
                    result = result_dict.get('SellerProfilePreferences').get('SupportedSellerProfiles').get('SupportedSellerProfile')
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
            message = "Error in Fetching Business Policies: %s" % e
            _logger.info('--------Error in Fetching Business Policies---------%r',e)
            status = False
        return {'status': status, 'message': message, 'result': result}

    @api.model
    def CreateBusinessPolicies(self, result, ChannelID):
        values = {}
        policy_obj = self.env['business.policies.mappings']
        created  = 0
        updated = 0
        msg = ''
        for record in result:
            values = {
                'name':record.get('ProfileName'),
                'policy_type':record.get('ProfileType'),
                'policy_id':record.get('ProfileID'),
                'description':record.get('ShortSummary'),
                'channel_id':ChannelID.id
            }
            exists = policy_obj.search([('channel_id','=',ChannelID.id),('policy_id','=',record.get('ProfileID'))])
            if not exists:
                policy_obj.create(values)
                created += 1
                if ChannelID.debug == 'enable':
                    _logger.info('-------%s debug policy created--------%r',record.get('ProfileName'))
            else:
                policy_obj.write(values)
                updated += 1
                if ChannelID.debug == 'enable':
                    _logger.info('-------%s debug policy updated--------%r',record.get('ProfileName'))
        if created:
            msg += '%s Business Policies have been created successfully!!! </br>'%created
        if updated:
            msg += '%s Business Policies have been updated successfully!!!'%updated
        return msg

    def import_now(self, ChannelID):
        final_message = ""
        context = dict(self._context or {})
        api_obj = self.env["multi.channel.sale"]._get_api(ChannelID, 'Trading')
        if api_obj['status']:
            business_policies = self._FetchEbayBusinessPolicies(api_obj['api'], ChannelID)
            final_message += business_policies.get('message')
            if business_policies['status']:
                final_message += self.with_context(context).CreateBusinessPolicies(
                    business_policies['result'], ChannelID)
        return final_message