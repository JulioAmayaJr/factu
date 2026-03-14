# -*- coding: utf-8 -*-

from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sv", "account.tax.group")
    def _get_sv_edi_account_tax_group(self):
        return {
            "tax_group_iva_retention": {"name": "IVA RETENIDO", "l10n_sv_edi_code": "IVA_RETE"},
            "tax-group_iva": {"name": "IVA", "l10n_sv_edi_code": "IVA"},
            "tax_group_iva_exempt": {"name": "EXENTO", "l10n_sv_edi_code": "IVA_EXEN"},
            "tax_group_iva_no_suj": {"name": "NO SUJETA", "l10n_sv_edi_code": "IVA_NO_SUJ"},
            "tax_group_iva_perception": {"name": "IVA PERCIBIDO", "l10n_sv_edi_code": "IVA_PER"},
            "tax_group_iva_export": {"name": "IVA EXPORTACIÓN", "l10n_sv_edi_code": "IVA_EXPO"},
            "tax_group_iva_import": {"name": "IVA IMPORTACIÓN", "l10n_sv_edi_code": "IVA_IMPO"},
        }
