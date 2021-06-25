# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
{
  "name"                 :  "Ebay ijVine",
  "summary"              :  "Configure your Ebay Store with odoo and manage backend operations in Odoo. Ebay Odoo Bridge integrates Ebay with Odoo you can import orders, products, etc from Ebay to Odoo",
  "category"             :  "Website",
  "version"              :  "4.4.4",
  "sequence"             :  1,
  "author"               :  "IjVine Corporation",
  "license"              :  "Other proprietary",
  "website"              :  "https://www.ijvine.com",
  "description"          :  """Ebay IjVine""",",
  "depends"              :  ['ijvine_ebay_base'],
  "data"                 :  [
                             'data/data.xml',
                             'views/business_policies_skeletion_view.xml',
                             'views/eob_config.xml',
                             'wizard/ebay_import_category_data_view.xml',
                             'wizard/ebay_import_product_data_view.xml',
                             'wizard/ebay_import_order_data_view.xml',
                             'views/inherited_search_views.xml',
                             'views/inherits_view.xml',
                             'data/ebay_import_cron.xml',
                             'views/dashboard_view_inherited.xml',
                             'wizard/odoo_export_products_view.xml',
                             'views/category_mapping_view.xml',
                             'views/feeds_view.xml',
                             'security/ir.model.access.csv',
                            ],
  "images"               :  ['static/description/banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "pre_init_hook"        :  "pre_init_check",
}