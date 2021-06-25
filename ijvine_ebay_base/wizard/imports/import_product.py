# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ImportProduct(models.TransientModel):
	_name = 'import.products'
	_description = 'Import Product'
	_inherit = 'import.operation'

	product_ids = fields.Text('Product ID(s)')
	source      = fields.Selection(
		selection=[
			('all','All'),
			('product_ids','Product ID(s)'),
		],
		required = True,
		default  = 'all'
	)
