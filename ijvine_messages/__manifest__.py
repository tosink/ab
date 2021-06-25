# -*- coding: utf-8 -*-
#################################################################################
# Author: IjVine Corporation (<https://ijvine.com/>).
# Copyright(c): 2021-Present IjVine Corporation (<https://ijvine.com/>).
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
{
	"name"         : "IjVine Message",
	"summary"      : """To show messages/warnings in Odoo""",
	"category"     : "Tools",
	"version"      : "1.0.0",
	"sequence"     : 1,
	"author"       : "IjVine Corporation (<https://ijvine.com/>).",
	"website"      : "https://ijvine.com",
	"description"  : """""",
	"data"         : [
		'security/ir.model.access.csv',
		'wizard/wizard_message.xml'
	],
	"installable"  : True,
	"pre_init_hook": "pre_init_check",
}
