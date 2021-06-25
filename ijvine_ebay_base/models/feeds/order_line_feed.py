# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import fields,models


class OrderLineFeed(models.Model):
	_name        = 'order.line.feed'
	_description = 'Order Line Feed'

	line_name                 = fields.Char('Product Name')
	line_product_uom_qty      = fields.Char('Quantity')
	line_price_unit           = fields.Char('Price')
	line_product_id           = fields.Char('Product ID')
	line_product_default_code = fields.Char('Default Code')
	line_product_barcode      = fields.Char('Barcode')
	line_taxes                = fields.Text('Taxes')
	order_feed_id             = fields.Many2one('order.feed','Order Feed ID')

	line_source = fields.Selection(
		selection = [
			('product','Product'),
			('delivery','Delivery'),
			('discount','Discount'),
		],
		default  = 'product',
		required = True
	)
	line_variant_ids = fields.Char(
		string  = 'Variant ID',
		default = 'No Variants',
		help    = """Attribute should  place in comma separated like color:red,color:blue,size:8,size:10"""
	)
