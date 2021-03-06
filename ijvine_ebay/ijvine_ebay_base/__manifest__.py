# -*- coding: utf-8 -*-
#################################################################################
# Author      : IjVine Corporation (<https://ijvine.com/>)
# Copyright(c): 2021-Present IjVine Corporation (<https://ijvine.com/>).
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################
{
  "name"                 :  "IjVine eBay Base",
  "summary"              :  """The module is Multiple platform connector with Odoo. You can connect and manage various platforms in odoo with the help of Odoo channel.""",
  "category"             :  "Website",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "IjVine Corporation",
  "license"              :  "Other proprietary",
  "website"              :  "https://ijvine.com",
  "description"          :  """IjVine Ebay Base""",
  "depends"              :  [
                             'delivery',
                             'ijvine_messages',
                            ],
  "data"                 :  [
                             'security/security.xml',
                             'security/ir.model.access.csv',
                             'wizard/wizard_message_view.xml',
                             'wizard/imports/import_operation.xml',
                             'wizard/exports/export_operation.xml',
                             'views/menus.xml',
                             'views/base/channel_order_states.xml',
                             'views/base/multi_channel_sale.xml',
                             'views/core/product_category.xml',
                             'views/core/product_template.xml',
                             'views/core/product_product.xml',
                             'views/core/product_pricelist.xml',
                             'views/core/res_partner.xml',
                             'views/core/sale_order.xml',
                             'views/core/res_config.xml',
                             'views/feeds/category_feed.xml',
                             'views/feeds/order_feed.xml',
                             'views/feeds/order_line_feed.xml',
                             'views/feeds/partner_feed.xml',
                             'views/feeds/product_feed.xml',
                             'views/feeds/variant_feed.xml',
                             'views/feeds/shipping_feed.xml',
                             'views/mappings/channel_synchronization.xml',
                             'views/mappings/account_journal_mapping.xml',
                             'views/mappings/account_mapping.xml',
                             'views/mappings/attribute_mapping.xml',
                             'views/mappings/attribute_value_mapping.xml',
                             'views/mappings/category_mapping.xml',
                             'views/mappings/order_mapping.xml',
                             'views/mappings/partner_mapping.xml',
                             'views/mappings/pricelist_mapping.xml',
                             'views/mappings/product_template_mapping.xml',
                             'views/mappings/product_variant_mapping.xml',
                             'views/mappings/shipping_mapping.xml',
                             'views/template.xml',
                             'wizard/exports/export_category.xml',
                             'wizard/exports/export_product.xml',
                             'wizard/exports/export_template.xml',
                             'wizard/update_mapping_wizard.xml',
                             'wizard/feed_wizard.xml',
                             'data/evaluation_action.xml',
                             'data/export_action.xml',
                             'data/update_mapping_action.xml',
                             'data/cron.xml',
                             'data/data.xml'
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "pre_init_hook"        :  "pre_init_check",
}
