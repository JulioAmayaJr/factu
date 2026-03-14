{
    "name": "Localización El Salvador",
    "version": "18.0.1.0.1",
    "summary": """
    Este módulo contiene la localización de El Salvador,
    con el fin de adaptar Odoo a las necesidades legales de este país.
    Distribución de municipios, departamentos, tipos de identificación,
    tipos de documentos, impuestos, etc.
    https://www.asamblea.gob.sv/node/12806
    También sirve como base para la emisión de facturas electrónicas
    DTE en El Salvador tgr_l10n_sv_edi.
     """,
    "countries": ["sv"],
    "category": "Accounting/Localizations/Account Charts",
    "author": "Juan D. Collado Vasquez",
    "website": "https://tagre.pe",
    "depends": [
        "base_vat",
        "base_address_extended",
        "l10n_latam_base",
        "l10n_latam_invoice_document",
        "account_debit_note",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_country.xml",
        "data/res.country.state.csv",
        "data/l10n_latam_identification_type_data.xml",
        "data/l10n_latam_document_type_data.xml",
        "data/res.city.csv",
        "data/l10n_sv.res.city.district.csv",
        "views/res_partner_views.xml",
        "views/account_tax_views.xml",
        "views/res_company_views.xml",
    ],
    "demo": [
        "demo/demo_company.xml",
        "demo/demo_partner.xml",
    ],
    "images": ["static/description/banner.png"],
    "price": 40.00,
    "currency": "USD",
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "uninstall_hook": "uninstall_hook",
}
