# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from . import models
from .  import wizard
def pre_init_check(cr):
	from openerp.service import common
	from openerp.exceptions import Warning
	version_info = common.exp_version()
	server_serie =version_info.get('server_serie')
	if server_serie!='13.0':raise Warning('Module support Odoo series 13.0 found {}'.format(server_serie))
	return True
