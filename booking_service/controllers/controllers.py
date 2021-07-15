# -*- coding: utf-8 -*-
# from odoo import http


# class BookingService(http.Controller):
#     @http.route('/booking_service/booking_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/booking_service/booking_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('booking_service.listing', {
#             'root': '/booking_service/booking_service',
#             'objects': http.request.env['booking_service.booking_service'].search([]),
#         })

#     @http.route('/booking_service/booking_service/objects/<model("booking_service.booking_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('booking_service.object', {
#             'object': obj
#         })
