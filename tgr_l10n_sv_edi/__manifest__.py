{
    "name": "Facturación electrónica para El Salvador",
    "version": "18.0.1.0.1",
    "summary": """
    Facturación electrónica para El Salvador (Metodo API externa)
     """,
    "countries": ["sv"],
    "category": "Accounting/Localizations/EDI",
    "author": "Juan D. Collado Vasquez",
    "website": "https://tagre.pe",
    "depends": [
        "tgr_l10n_sv",
        "account_edi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/certificate_security.xml",
        # data
        "data/account_edi_format.xml",
        "data/l10n_sv.cat.019.csv",
        "data/uom_data.xml",
        # views
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "wizards/account_invoice_refund_views.xml",
        "wizards/account_cancel_wizard_views.xml",
        # "views/l10n_sv_cat_019_views.xml",
        "views/report_invoice.xml",
        "views/account_move_views.xml",
        "views/account_tax_views.xml",
        "views/res_company_views.xml",
        "views/l10n_sv_certificate_views.xml",
    ],
    "demo": [
        "./demo/demo_company.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # 'tgr_l10n_sv/static/src/**/*'
        ],
    },
    "external_dependencies": {"python": ["cryptography", "pyjwt", "xmltodict"]},
    "images": ["static/description/banner.png"],
    "price": 920.00,
    "currency": "USD",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
    # "uninstall_hook": "uninstall_hook",
}
