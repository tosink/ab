# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import api,fields,models

class ImportAttributeValue(models.TransientModel):
	_name = 'import.attributes.value'
	_description = 'Import Attribute Value'
	_inherit = 'import.operation'

	attribute_value_ids = fields.Text('Attribute Value ID(s)')
