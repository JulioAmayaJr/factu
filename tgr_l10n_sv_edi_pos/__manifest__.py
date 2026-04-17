# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Facturación Electrónica pala El Salvador POS",
    "version": "18.0.1.0.1",
    "category": "Accounting/Localizations/Point of Sale",
    "author": "Juan D. Collado Vasquez",
    "countries": ["sv"],
    "description": """
    "website": "https://tagre.pe",
    """,
    "depends": [
        "tgr_l10n_sv",
        "tgr_l10n_sv_edi",
        "point_of_sale",
    ],
    "data": [
        "data/res_partner_data.xml",
        "views/templates.xml",
        "views/pos_order_views.xml",
        "views/res_config_settings_view.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": ["tgr_l10n_sv_edi_pos/static/src/**/*"],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
    "license": "LGPL-3",
    "price": 200.00,
    "currency": "USD",
}
