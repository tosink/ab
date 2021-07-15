# -*- coding: utf-8 -*-
{
    'name': "booking_service",

    'summary': """To allow users to create bookings for employees and equipments""",

    'description': """
        To allow users to create bookings for employees and equipments
    """,

    'author': "Ahmed Gaber",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'hr', 'calendar'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/employee.xml',
        'views/calendar_event.xml',
        'views/booking_team_view.xml',
        'views/booking_order_view.xml',
        'views/menus.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
