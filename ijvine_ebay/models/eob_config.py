# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2021-Present IjVine Corporation (<https://ijvine.com/>)
#
#################################################################################
from odoo import fields, models, api, _
from odoo import tools, api
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from datetime import datetime, timedelta
try:
    from ..ebaysdk.trading import Connection as Trading
except Exception as e:
    _logger.info('------Install Ebaysdk-----Run on terminal "pip install ebaysdk"-------')
    pass


EBAY_GLOBAL_SITE_IDS = [
    ('0', 'eBay United States - EBAY-US'),
    ('2', 'eBay Canada(English) - EBAY-ENCA'),
    ('3', 'eBay UK - EBAY-GB'),
    ('15', 'eBay Australia - EBAY-AU'),
    ('16', 'eBay Austria - EBAY-AT'),
    ('23', 'eBay Belgium(French) - EBAY-FRBE'),
    ('71', 'eBay France - EBAY-FR'),
    ('77', 'eBay Germany - EBAY-DE'),
    ('100', 'eBay Motors - EBAY-MOTOR'),
    ('101', 'eBay Italy - EBAY-IT'),
    ('123', 'eBay Belgium(Dutch) - EBAY-NLBE'),
    ('146', 'eBay Netherlands - EBAY-NL'),
    ('186', 'eBay Spain - EBAY-ES'),
    ('193', 'eBay Switzerland - EBAY-CH'),
    ('201', 'eBay Hong Kong - EBAY-HK'),
    ('203', 'eBay India - EBAY-IN'),
    ('205', 'eBay Ireland - EBAY-IE'),
    ('207', 'eBay Malaysia - EBAY-MY'),
    ('210', 'eBay Canada(French) - EBAY-FRCA'),
    ('211', 'eBay Philippines - EBAY-PH'),
    ('212', 'eBay Poland - EBAY-PL'),
    ('216', 'eBay Singapore - EBAY-SG')
]

DOMAIN_APIS = {
    'production'	: {
        'finding': 'svcs.ebay.com',
        'trading': 'api.ebay.com',
        'shopping': 'open.api.ebay.com',
        'merchandising': 'svcs.ebay.com'
    },
    'sandbox'		: {
        'finding': 'svcs.sandbox.ebay.com',
        'trading': 'api.sandbox.ebay.com',
        'shopping': 'open.api.sandbox.ebay.com',
        'merchandising': 'svcs.sandbox.ebay.com'
    }
}
CRON_INTERVAL_TYPE = [
    ('minutes', 'Minutes'),
    ('hours', 'Hours'),
    ('days', 'Days'),
    ('weeks', 'Weeks'),
    ('months', 'Months')
]
CRON_STATE = [
    ('stop', 'Stop'),
    ('start', 'Start')
]

EBAY_CONDITION_IDS = [
    ('1000', 'NEW'),
    ('3000', 'USED'),
    ('5000', 'GOOD'),
    ('4000', 'VERY GOOD'),
    ('1750', 'NEW WITH DEFECTS'),
    ('2000', 'MANUFACTURER REFURBISHED'),
    ('2500', 'SELLER REFURBISHED'),
    ('6000 ', 'ACCEPTABLE'),
    ('7000', 'FOR PARTS OR NOT WORKING'),

]
def _unescape(text):
        ##
        # Replaces all encoded characters by urlib with plain utf8 string.

        # @param text source text.
        # @return The plain text.
    from urllib import unquote_plus
    return unquote_plus(text.encode('utf8'))


class EbayGlobalIdValues(models.Model):
    _name = "ebay.global.id.values"
    _description = "Ebay Global Ids"
    name = fields.Char(
        compute='_compute_name')
    site_name = fields.Char(
        required=True,
        string="Site Name",
        size=100)
    global_id = fields.Char(
        required=True,
        string="Global ID",
        size=50)
    territory = fields.Char(
        string="Territory",
        size=2)
    ebay_site_id = fields.Integer(
        string="eBay Site ID")

    def _compute_name(self):
        for record in self:
            record.name = record.site_name + ' - ' + record.global_id


class MultiChannelSale(models.Model):
    _inherit = "multi.channel.sale"

    @api.model
    def get_channel(self):
        res = super(MultiChannelSale, self).get_channel()
        res.append(("ebay", "Ebay"))
        return res

    
    def _get_api(self,  ChannelObj, api_domain='Trading'):
        status = True
        message = ''
        api = ''
        # active_obj = self.search([('active', '=', True),('channel','=','ebay')], limit=1)
        if ChannelObj and ChannelObj.active:
            try:
                debug = False
                if ChannelObj.debug == 'enable':
                    debug = True
                if api_domain == 'Trading':
                    api = Trading(debug=debug, warnings=debug, timeout=360, config_file=False, domain=DOMAIN_APIS[ChannelObj.environment][
                                  'trading'], appid=ChannelObj.ebay_appid, devid=ChannelObj.ebay_devid, certid=ChannelObj.ebay_certid, token=ChannelObj.ebay_token,siteid=str(ChannelObj.ebay_global_value_id.ebay_site_id))
                    if api.error():
                        message = message + "Error: %s <br>" % api.error()
                        status = False
                else:
                    message = message + "Error: UNKNOWN API DOMAIN <br>"
                    status = False
            except Exception as e:
                message = message + "Error: %s <br>" % e
                status = False
        else:
            message = message + "Error: NO ACTIVE CONFIGURATION FOUND !!! <br>"
            status = False
        return {'api': api, 'status': status, 'message': message}

 
    def test_ebay_connection(self):
        for obj in self:
            if obj.channel == 'ebay':
                status = True
                t_message = '<h2> Testing Trading API </h2><br>'
                f_message = '<h2> Testing Finding API </h2><br>'
                s_message = '<h2> Testing Shopping API </h2><br>'
                m_message = '<h2> Testing Merchandising API </h2><br>'
                final_message = ""
                debug = False
                if obj.debug == 'enable':
                    debug = True
                try:
                    t_api = Trading(debug=debug, warnings=debug, timeout=360, config_file=False, domain=DOMAIN_APIS[obj.environment][
                                    'trading'], appid=obj.ebay_appid, devid=obj.ebay_devid, certid=obj.ebay_certid, token=obj.ebay_token,siteid=str(obj.ebay_global_value_id.ebay_site_id))
                    t_response = t_api.execute('GetUser', {})
                    t_message = t_message + 'CODE : %s <br>' % t_api.response_code()
                    t_message = t_message + 'STATUS : %s <br>' % t_api.response_status()
                    if t_api.error():
                        t_message = t_message + "Error: %s <br>" % t_api.error()
                        status = False
                        obj.state = 'error'
                except Exception as e:
                    t_message = t_message + "Unknown Error...%s<br>" % str(e)
                    status = False
                final_message = final_message + t_message
                if status:
                    final_message = "All tests passed successfully. You can start synchronizing from your ebay store now."
                    obj.state = 'validate'
                wizard_id = self.env['wizard.message'].create(
                    {'text': final_message})
            return {'name': _("Summary"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'wizard.message',
                    'res_id': wizard_id.id,
                    'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                            'domain': '[]',
                    }
    @api.model
    def get_ebay_default_category(self):
        domain = self.env['channel.category.mappings'].search([('ecom_store','=','ebay'),('leaf_category','=',True)]).ids
        return [('id', 'in', domain)]

    @api.model
    def _get_default_data(self, ChannelObj):
        data = {}
        status = False
        message = ""
        if ChannelObj and ChannelObj.active:
            data['ebay_cat_site_id'] = ChannelObj.ebay_global_value_id.ebay_site_id
            data['ebay_sellerid'] = ChannelObj.ebay_sellerid
        else:
            message = message + "Error: NO ACTIVE CONFIGURATION FOUND !!! <br>"
            status = False
        return {'data': data, 'status': status, 'message': message}

    ebay_global_value_id = fields.Many2one(
        comodel_name='ebay.global.id.values',
        string='Ebay Site')
    ebay_appid = fields.Char(
        string='Ebay App ID',
        size=50,
        help="36 bit key")
    ebay_sellerid = fields.Char(
        string='Ebay Seller ID',
        size=50,
        help="Your unique seller ID")
    ebay_devid = fields.Char(
        string='Ebay Dev ID',
        size=50,
        help="36 bit key")
    ebay_certid = fields.Char(
        string='Ebay Cert ID',
        size=50,
        help="36 bit key")
    ebay_token = fields.Text(
        string='Ebay User Token')
    active = fields.Boolean(
        string='Active',
        default=True)
    

    ####################################  ebay product export configuration ################################################
    
    ebay_return_accepted_option = fields.Selection(
        [('ReturnsAccepted', 'ReturnsAccepted'),
            ('ReturnsNotAccepted', 'ReturnsNotAccepted')],
        string='Returns Accepted Option',
        default="ReturnsAccepted",
    help="Weather to accept the returns for this producr or not")
    ebay_return_within_option = fields.Selection(
        [('Days_3', '3 Days'), ('Days_7', '7 Days'), ('Days_10', '10 Days'),
         ('Days_14', '14 Days'), ('Months_1', '1 Month'), ('Days_60', '2 Months')],
        default="Days_10",
        string='Returns Within Options',
        help="Return the the product within how much time")
    ebay_shipping_cost_paid_by = fields.Selection(
        [('Buyer', 'Buyer'), ('Seller', 'Seller')],
        string='Shipping CostPaid By Option',
        default="Buyer",
        help="Who will pay the shipping cost of the return")
    ebay_return_description = fields.Text(
        'Additional Information',
        help="Add some Additional information regarding your Return Policy",
        default="This is a test return description")
    ebay_shipping_service = fields.Many2one(
        comodel_name='channel.shipping.mappings',
        string='Shipping Method',
        domain=[('ecom_store', '=', 'ebay')],
        help="Shipping service for exporting the products to odoo.These must be fetched from ebay before exporting the product to odoo.")
    ebay_shipping_cost = fields.Float(
        string='Shipping Service Cost',
        help="Cost of the shipping service used with the Product")
    ebay_shipping_additional_cost = fields.Float(
        string="Shipping Service Additional Cost",
        help="The cost of shipping each additional item if the same buyer purchases multiple quantity of the same line item. This field is required when creating a multiple-quantity, fixed-price listing.")
    ebay_shipping_priority = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        string='Shipping Service Priority',
        default="1",
        help="This integer value controls the order (relative to other shipping services) in which the corresponding ShippingService will appear in the View Item and Checkout page.")
    ebay_dispatch_time_max = fields.Selection(
        [('0', 'Same Day'),('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('10', '10'),
         ('20', '20'), ('30', '30')],
        string='DispatchTimeMax',
        help="Specifies the maximum number of business days the seller commits to for preparing an item to be shipped after receiving a cleared payment.")
    default_ebay_category_id = fields.Many2one(
        comodel_name='channel.category.mappings',
        string='Default Category',
        domain=[('leaf_category', '=', True)],
        help="Default category if the category of some proudt does not match.")
    ebay_payment_method = fields.Many2one(
        comodel_name='channel.account.journal.mappings',
        string='Payment Method',
        domain=[('ecom_store', '=', 'ebay')],
        help="Identifies the payment method (such as PayPal) that the seller will accept when the buyer pays for the item.")
    ebay_payment_method_related = fields.Char(
        related='ebay_payment_method.name',
        string="Payment_method")
    paypal_email_address = fields.Char(
        string='PayPalEmailAddress',
        default="test@paypal.com",
        help="Valid PayPal email address for the PayPal account that the seller will use if they offer PayPal as a payment method for the listing. eBay uses this to identify the correct PayPal account when the buyer pays via PayPal during the checkout process")
    ebay_listing_duration = fields.Selection(
        [('GTC', 'GOOD TILL CANCELLED'), ('Days_1', '1 Days'), ('Days_3', '3 Days'), ('Days_5', '5 Days'), ('Days_10', '10 Days'), ('Days_30', '30 Days')], string='Listing Duration', default='GTC', help="Describes the number of days the seller wants the listing to be active.")
    ebay_export_variant_images = fields.Boolean(
        string='Export Variant Images',
        help='In order to export the products quicly set it false.')
    ebay_display_product_url  = fields.Boolean('Display Ebay URL Of Exported Products')
    ###############################  fields to set the cron orders#############################################
    ebay_order_cron_template = fields.Many2one(
        comodel_name='ir.cron',
        string='Set Cron For Orders')
    ebay_order_cron_interval_number = fields.Integer(
        string='Interval Number',
        default=1,
        help="Repeat every x.")
    ebay_order_cron_interval_type = fields.Selection(
        CRON_INTERVAL_TYPE,
        string='Interval Unit',
        help='Type of the interval',
        default="hours")
    ebay_order_cron_state = fields.Selection(
        CRON_STATE,
        string='Cron State',
        help="State of the cron(stop, start)")
    ebay_order_cron_nxtcall = fields.Datetime(
        string='Next Execution Date',
        default=datetime.now(),
        help="This fields is taken as the CreateDateTo for fetching the orders from ebay. And the CreateDatefrom is taken as value of Interval Number before CreateDateTo.")
    ebay_configure_order_cron = fields.Selection(
        [('yes', 'Yes'), ('no', 'NO')],
        default="no",
        string='Do you want to Configure Cron to Import Orders',
        help="Configure the cron for importing Orders from ebay")
    #####################  fields to set the cron products ##########################################
    ebay_product_cron_template = fields.Many2one(
        comodel_name='ir.cron',
        string='Set Cron For Products')
    ebay_product_cron_interval_number = fields.Integer(
        string='Interval Number',
        default=1,
        help="Repeat every x.")
    ebay_product_cron_interval_type = fields.Selection(
        CRON_INTERVAL_TYPE,
        string='Interval Unit',
        help='Type of the interval',
        default="hours")
    ebay_product_cron_state = fields.Selection(
        CRON_STATE,
        string='Cron Operation',
        help="State of the cron(stop, start)")
    ebay_start_date_nextcall = fields.Datetime(
        string='Next Execution Date',
        default=datetime.now(),
        help="This fields is taken as the StartDateTo for fetching the products from ebay. And the StartDateFrom is taken as value of Interval Number before StartDateTo.")
    ebay_product_store_category_id = fields.Many2one(
        comodel_name='channel.category.mappings',
        string='Ebay Category',
        domain="[('category_name','!=',False)]",
        help="Ebay Category From which you want to import ,if none imports irrespective of the category")
    configure_product_cron = fields.Selection(
        [('yes', 'Yes'), ('no', 'NO')],
        string='Do you want to Configure Cron to Import Products',
        default="no",
        help="Configure the cron for importing proucts from ebay")
    ebay_order_status = fields.Selection(
        [('Active', 'Active'), ('Completed', 'Completed'), ('Canceled', 'Canceled')],
        string='Ebay Order Status',
        default="Completed",
        help="The field is used to retrieve orders that are in a specific state.")
    
    ebay_business_policies = fields.Selection(
        [('existing', 'Existing'), ('custom', 'Custom')],
        string='Business Policies to be used',
        default="custom",
        help="If you want to use the existing payment ebay policy. Import all the existing policies and select one of them.")
    ebay_existing_payment_policy = fields.Many2one(
        comodel_name="business.policies.mappings",
        string="Payment Policy",
        domain=[('policy_type','=','PAYMENT')],
        help="Select the payment Policy you wnt to use for creating a listing on ebay"
    )
   
    ebay_existing_shipping_policy = fields.Many2one(
        comodel_name="business.policies.mappings",
        string="Shipping Policy",
        domain=[('policy_type','=','SHIPPING')],
        help="Select the shipping Policy you wnt to use for creating a listing on ebay"
    )
    ebay_existing_return_policy = fields.Many2one(
        comodel_name="business.policies.mappings",
        string="Return Policy",
        domain=[('policy_type','=','RETURN_POLICY')],
        help="Select the return Policy you wnt to use for creating a listing on ebay"
    )

    ebay_use_html_description = fields.Boolean(
        string="Use description in HTML format",
        help="check this if you want to use the description of/for ebay in HTML format."
    )
    ebay_default_export_quantity = fields.Integer(
        string="Default Quantity to Export",
        default=1,
        help="Default to export when quantity of the product is zero"
    )
    ebay_default_category = fields.Many2one(
        comodel_name = 'channel.category.mappings',
        string="Ebay Default Category",
        domain=lambda self:self.env['multi.channel.sale'].get_ebay_default_category(),
        help="Default Category if the category is not specified"
    )
    ebay_condition_id = fields.Selection(
        EBAY_CONDITION_IDS,
        string='Product Condition',
        help='Condition of the product to be exported',
        default="1000", 
        )
    @api.onchange('ebay_configure_order_cron', 'ebay_order_cron_state')
    def _onchange_ebay_configure_order_cron(self):
        if self.ebay_configure_order_cron == 'no':
            self.ebay_order_cron_state = 'stop'
        return

    @api.onchange('configure_product_cron', 'ebay_product_cron_state')
    def _onchange_configure_product_cron(self):
        if self.configure_product_cron == 'no':
            self.ebay_product_cron_state = 'stop'
        return

    # @api.onchange('ebay_configure_category_cron', 'ebay_category_cron_state')
    # def _onchange_ebay_configure_category_cron(self):
    #     if self.ebay_configure_category_cron == 'no':
    #         self.ebay_category_cron_state = 'stop'
    #     return


    def import_ebay_shipping_methods(self):
        message = self.env['import.ebay.shipping.methods'].import_now(self)
        return self.env['multi.channel.sale'].display_message(message)


    def import_ebay_business_policies(self):
        message = self.env['ebay.import.business.policies'].import_now(self)
        _logger.info('-------------rrr----')
        return self.env['multi.channel.sale'].display_message(message)


    def import_products_cron_start(self):
        ir_model_data = self.env['ir.model.data']
        interval_number = self.ebay_product_cron_interval_number
        interval_type = self.ebay_product_cron_interval_type
        if int(interval_number) < 1:
            raise UserError('Value of Interval Number can`t be negative or 0.')
        if not interval_type:
            raise UserError('You must select Interval Type.')
        try:
            cron_id = ir_model_data.get_object_reference(
                'ijvine_ebay', 'ir_cron_import_eaby_products')[1]
            cron_obj = self.env["ir.cron"].browse(cron_id)
            cron_obj.write(
                {'active': True, 'interval_number': interval_number, 'interval_type': interval_type, 'nextcall': self.ebay_start_date_nextcall})
            self.write({'ebay_product_cron_state': 'start'})
            return True
        except Exception as e:
            raise UserError("Error: %s" % e)


    def import_products_cron_stop(self):
        ir_model_data = self.env['ir.model.data']
        try:
            cron_id = ir_model_data.get_object_reference(
                'ijvine_ebay', 'ir_cron_import_eaby_products')[1]
            cron_obj = self.env["ir.cron"].browse(cron_id)
            cron_obj.write({'active': False})
            self.write({'ebay_product_cron_state': 'stop'})
            return True
        except Exception as e:
            raise UserError("Error: %s" % e)

    def import_orders_cron_start(self):
        ir_model_data = self.env['ir.model.data']
        interval_number = self.ebay_order_cron_interval_number
        interval_type = self.ebay_order_cron_interval_type
        nextcall = self.ebay_order_cron_nxtcall
        if int(interval_number) < 1:
            raise UserError('Value of Interval Number can`t be negative or 0.')
        if not interval_type:
            raise UserError('You must select Interval Type.')
        try:
            cron_id = ir_model_data.get_object_reference(
                'ijvine_ebay', 'ir_cron_import_eaby_orders')[1]
            cron_obj = self.env["ir.cron"].browse(cron_id)
            cron_obj.write({'active': True, 'interval_number': interval_number,
                            'interval_type': interval_type, 'nextcall': nextcall})
            self.write({'ebay_order_cron_state': 'start'})
            return True
        except Exception as e:
            raise UserError("Error: %s" % e)

    def import_orders_cron_stop(self):
        ir_model_data = self.env['ir.model.data']
        try:
            cron_id = ir_model_data.get_object_reference(
                'ijvine_ebay', 'ir_cron_import_eaby_orders')[1]
            cron_obj = self.env["ir.cron"].browse(cron_id)
            cron_obj.write({'active': False})
            self.write({'ebay_order_cron_state': 'stop'})
            return True
        except Exception as e:
            raise UserError("Error: %s" % e)
