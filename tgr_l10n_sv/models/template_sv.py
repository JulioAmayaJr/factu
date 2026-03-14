from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("sv")
    def _get_pe_template_data(self):
        return {
            "property_account_receivable_id": "char1102",
            "property_account_payable_id": "char2101",
            "property_account_expense_categ_id": "char4102",
            "property_account_income_categ_id": "char5101",
            "property_stock_account_input_categ_id": "char4201",
            "property_stock_account_output_categ_id": "char4201",
            "property_stock_valuation_account_id": "char1103",
            "property_stock_account_production_cost_id": "char1105",
            "code_digits": "8",
        }

    @template("sv", "res.company")
    def _get_pe_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.sv",
                "l10n_sv_establishment_type": "02",
                "anglo_saxon_accounting": True,
                "bank_account_code_prefix": "110102",
                "cash_account_code_prefix": "110102",
                "transfer_account_code_prefix": "1101",
                "account_default_pos_receivable_account_id": "char1102",
                # "income_currency_exchange_account_id": "income_currency_exchange",
                # "expense_currency_exchange_account_id": "expense_currency_exchange",
                # "default_cash_difference_income_account_id": "cash_diff_income",
                # "default_cash_difference_expense_account_id": "cash_diff_expense",
                "account_sale_tax_id": "sale_tax_iva_13",
                "account_purchase_tax_id": "purchase_tax_iva_13",
            },
        }
