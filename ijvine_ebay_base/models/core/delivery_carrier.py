# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)

##############################################################################
from odoo import fields,models


class DeliveryCarrier(models.Model):
	_inherit = 'delivery.carrier'

	channel_mapping_ids = fields.One2many(
		string       = 'Mappings',
		comodel_name = 'channel.shipping.mappings',
		inverse_name = 'odoo_shipping_carrier',
		copy         = False
	)
