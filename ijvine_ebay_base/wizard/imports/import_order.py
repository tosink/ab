# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ImportOrder(models.TransientModel):
	_name = 'import.orders'
	_description = 'Import Order'
	_inherit = 'import.operation'

	source = fields.Selection(
		selection=[
			('all','All'),
			('order_ids','Order ID(s)'),
		],
		required = True,
		default  = 'all'
	)

	order_ids = fields.Text('Order ID(s)')
