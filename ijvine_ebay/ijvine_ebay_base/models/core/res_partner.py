# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import fields,models


class ResPartner(models.Model):
	_inherit = 'res.partner'

	channel_mapping_ids = fields.One2many(
		string       = 'Mappings',
		comodel_name = 'channel.partner.mappings',
		inverse_name = 'odoo_partner',
		copy         = False
	)
