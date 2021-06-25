# -*- coding: utf-8 -*-
################################################################################
#
#   Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
################################################################################
from odoo import models
import logging
_logger = logging.getLogger(__name__)


class WizardMessage(models.TransientModel):
    _inherit = "wizard.message"

    def operation_back(self):
        ctx = dict(self._context or {})
        _logger.info("======================: %r", self._context)
        partial = self.env['import.operation'].browse(ctx.get('active_id'))
        ctx['active_id'] = False
        ctx['default_channel_id'] = False
        return {'name': "Import Operation",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'import.operation',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }