# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ImportTemplate(models.TransientModel):
	_name = 'import.templates'
	_description = 'Import Template'
	_inherit = 'import.operation'

	product_tmpl_ids = fields.Text('Product Template ID(s)')
	source           = fields.Selection(
		selection=[
			('all','All'),
			('product_tmpl_ids','Product ID(s)'),
		],
		required = True,
		default  = 'all'
	)
