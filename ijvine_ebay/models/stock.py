# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import tools, api
from odoo import fields as Fields, models
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def update_ebay_stock_realtime(self, ebayProdId, ebayVarId, prodQty, instanceObj):
        res_dict = self.env['import.ebay.products'].get_product_data_using_product_id(ebayProdId, instanceObj)
        result = res_dict.get('result')
        if isinstance(result, (list)):
            result = result[0]
        ebayQty = result.get('Quantity')
        updatedQty =  float(ebayQty) + prodQty
        Variations = {}
        if result.get('Variations'):
            variations = result.get('Variations').get('Variation')
            for variation in variations:
                attrString =  self.env['import.ebay.products']._CreateAttributeString(variation)
                new_variation = {}
                if ebayVarId == attrString:
                    updatedQty =  float(variation.get('Quantity')) + prodQty
                    new_variation.update({'Quantity':int(updatedQty)})
                    new_variation.update({'VariationSpecifics':variation.get('VariationSpecifics')})
                    self.env['export.templates'].update_ebay_quantity_real_time(ebayProdId, instanceObj, updatedQty, new_variation)
        self.env['export.templates'].update_ebay_quantity_real_time(ebayProdId, instanceObj, updatedQty)
        return True

    def multichannel_sync_quantity(self, pick_details):
        """
        Overriden method for real time synchroniztion of the quantity from odoo to ebay.
        """
        prodObj = self.env['product.product'].browse(pick_details.get('product_id'))
        prodQty = pick_details.get('product_qty')
        mappingObjs = prodObj.channel_mapping_ids
        res = self.env['export.templates']._get_variations(prodObj.product_tmpl_id)
        for mappingObj in mappingObjs:
            instanceObj = mappingObj.channel_id
            if mappingObj.ecom_store == 'ebay' and instanceObj.auto_sync_stock:
                if pick_details.get('source_loc_id') == instanceObj.location_id.id:
                    prodQty = -(prodQty)

                ebayProdId = mappingObj.store_product_id
                ebayVarId  = mappingObj.store_variant_id

                self.update_ebay_stock_realtime(ebayProdId, ebayVarId, prodQty, instanceObj)
        return super(StockMove, self).multichannel_sync_quantity(pick_details)
