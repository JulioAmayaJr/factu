from datetime import datetime
from zoneinfo import ZoneInfo
from odoo import api, models
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_round, float_repr

CAT_11_MAPPING = {"consu": 1, "combo": 1, "service": 2}


class MixinDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.mixin"
    _description = "Documento Electrónico Mixin"

    name = ""
    _version = 3
    _tipoDte = None

    @api.model
    def generate_json(self, invoice, credentials):
        raise NotImplementedError("Debes implementar 'generate_json' en las subclases.")

    def _get_identificacion(self, invoice, credentials):
        return {
            "version": self._version,
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "tipoDte": self._tipoDte,
            "numeroControl": invoice.tgr_l10n_sv_edi_numero_control or "",
            "codigoGeneracion": invoice.tgr_l10n_sv_edi_codigo_generacion or "",
            "tipoModelo": 1,
            "tipoOperacion": 2 if invoice.contingency_event else 1,
            "tipoContingencia": (int(invoice.contingency_type) if invoice.contingency_event else None),
            "motivoContin": (invoice.contingency_reason if invoice.contingency_event else None),
            "fecEmi": invoice.invoice_date.strftime("%Y-%m-%d"),
            # "horEmi": invoice.invoice_date.strftime("%H:%M:%S"),
            "horEmi": datetime.now(ZoneInfo("America/El_Salvador")).strftime("%H:%M:%S"),
            "tipoMoneda": invoice.currency_id.name,
        }

    def _get_emisor(self, invoice):
        company = invoice.company_id
        partner = company.partner_id
        root_company = company.l10n_sv_edi_get_root_company()
        root_partner = root_company.partner_id

        return {
            "nit": root_partner.vat,
            "nrc": root_partner.l10n_sv_nrc,
            "nombre": root_partner.name,
            "codActividad": root_partner.l10n_sv_edi_economic_activity_id.code or None,
            "descActividad": root_partner.l10n_sv_edi_economic_activity_id.name or None,
            "nombreComercial": company.name,
            "tipoEstablecimiento": (
                company.partner_id.l10n_sv_edi_establishment_type if company.partner_id.l10n_sv_edi_establishment_type else "02"
            ),
            "direccion": self._get_common_direccion(partner),
            "telefono": partner.phone,
            "correo": partner.email,
        }

    def _get_receptor(self, invoice):
        partner = invoice.partner_id
        return {
            "nit": partner.vat or None,
            "nrc": partner.l10n_sv_nrc or None,
            "nombre": partner.name,
            "codActividad": partner.l10n_sv_edi_economic_activity_id.code if partner.l10n_sv_edi_economic_activity_id else None,
            "descActividad": partner.l10n_sv_edi_economic_activity_id.name if partner.l10n_sv_edi_economic_activity_id else None,
            "nombreComercial": partner.display_name,
            "direccion": self._get_common_direccion(partner),
            "telefono": partner.phone or None,
            "correo": partner.email or None,
        }

    def _get_documento_relacionado(self, invoice):
        return None

    def _get_cuerpo_documento(self, values):
        raise NotImplementedError('Debes implementar "_get_cuerpo_documento" en las subclases.')

    def _get_cuerpo_documento_common_line(self, item):
        """ """
        line = item.get("line", False)
        common_line = {
            "numItem": item["index"],
            "tipoItem": CAT_11_MAPPING.get(line.product_id.product_tmpl_id.type, 1) if line else None,
            "numeroDocumento": None,
            "codigo": (line.product_id.default_code if line.product_id.default_code else None) if line.product_id else None,
            "codTributo": None,
            "descripcion": line.product_id.display_name if line.product_id else line.name,
            "cantidad": line.quantity,
            "uniMedida": (
                (
                    99
                    if line.product_id.product_tmpl_id.type == "service"
                    else (line.product_id.product_tmpl_id.uom_id.l10n_sv_edi_measure_unit_code or 99)
                )
                if line.product_id
                else 99
            ),
        }
        return common_line

    def _get_resumen(self, values):
        total_no_suj = 0.00
        total_exenta = 0.00
        total_gravada = 0.00
        sub_total_ventas = 0.00
        sub_total = 0.00
        totalDescu = 0.00
        tributos = []
        iva_rete1 = 0.00
        for tax_key, tax_data in values["tax_details_grouped"]["tax_details"].items():
            print(tax_data)
            if tax_key["l10n_sv_edi_code"] == "IVA":
                total_gravada += tax_data["base_amount_currency"]
            if tax_key["l10n_sv_edi_code"] == "IVA_RETE":
                iva_rete1 += tax_data["tax_amount_currency"] * -1
            if tax_key["l10n_sv_edi_tax_code"]:
                tributos.append(
                    {
                        "codigo": tax_key["l10n_sv_edi_tax_code"],
                        "descripcion": tax_key["l10n_sv_edi_tax_invoice_label"],
                        "valor": tax_data["tax_amount_currency"],
                    }
                )
        sub_total_ventas = values["tax_details_grouped"]["base_amount_currency"] or 0.00
        sub_total = sub_total_ventas
        for item in values["invoice_line_vals_list"]:
            totalDescu += item["price_discount"]
        return {
            "totalNoSuj": float_round(total_no_suj, 2),
            "totalExenta": float_round(total_exenta, 2),
            "totalGravada": float_round(total_gravada, 2),
            "subTotalVentas": float_round(sub_total_ventas, 2),
            "descuNoSuj": 0.00,
            "descuExenta": 0.00,
            "descuGravada": 0.00,
            "totalDescu": float_round(totalDescu, 2),
            "tributos": tributos,
            "subTotal": float_round(sub_total, 2),
            "ivaPerci1": 0.00,
            "ivaRete1": float_round(iva_rete1, 2),
            "reteRenta": 0.00,
            "montoTotalOperacion": float_round(values["record"].amount_total + iva_rete1, 2),
            "totalLetras": str(values["record"]._l10n_sv_edi_amount_to_text()).replace("DOLLARS", "DÓLARES").replace("CENTS", "CENTAVOS"),
            "condicionOperacion": 1,
        }

    def _get_extension(self, invoice):
        return {
            "nombEntrega": None,
            "docuEntrega": None,
            "nombRecibe": None,
            "docuRecibe": None,
            "observaciones": None,
            "placaVehiculo": None,
        }

    def _get_apendice(self, invoice):
        return None

    def _get_common_direccion(self, partner_id):
        if not partner_id.state_id or not partner_id.city_id or not partner_id.street:
            return None
        return {
            "departamento": partner_id.state_id.code or None,
            "municipio": partner_id.city_id.l10n_sv_code or None,
            "complemento": partner_id.street or None,
        }

    def _l10n_sv_edi_get_dte_values(self, invoice):
        price_precision = self.env["decimal.precision"].precision_get("Product Price")
        precision_rounding = 0.01

        def clean_amount(value, precision_digits=None, precision_rounding=None):
            return (
                0.00
                if float_is_zero(value, precision_digits, precision_rounding)
                else float_round(value, precision_digits, precision_rounding)
            )

        invoice_date_due_vals_list = []
        for index, rec_line in enumerate(
            invoice.line_ids.filtered(lambda l: l.account_type == "asset_receivable"),
            start=1,
        ):
            amount = rec_line.amount_currency
            invoice_date_due_vals_list.append(
                {
                    "code": f"{index:02d}",
                    "amount": rec_line.move_id.currency_id.round(amount),
                    "currency_name": rec_line.move_id.currency_id.name,
                    "date_maturity": rec_line.date_maturity,
                }
            )

        values = {
            **invoice._prepare_edi_vals_to_export(),
            "is_refund": invoice.move_type in ("out_refund", "in_refund"),
            "invoice_date_due_vals_list": invoice_date_due_vals_list,
            "precision_rounding": precision_rounding,
        }
        # Invoice lines
        for line_vals in values["invoice_line_vals_list"]:
            line = line_vals["line"]
            line_vals["price_subtotal_unit"] = (
                clean_amount(
                    line.price_subtotal / line.quantity,
                    precision_rounding=precision_rounding,
                )
                if line.quantity
                else 0.00
            )
            line_vals["price_total_unit"] = (
                clean_amount(
                    line.price_total / line.quantity,
                    precision_rounding=precision_rounding,
                )
                if line.quantity
                else 0.00
            )
            line_vals["price_discount"] = clean_amount(line_vals["price_discount"], precision_rounding=precision_rounding)
            line_vals["price_discount_unit"] = clean_amount(line_vals["price_discount_unit"], precision_rounding=precision_rounding)

        # Tax Details
        def grouping_key_generator(base_line, tax_data):
            tax = tax_data["tax"]
            return {
                "l10n_sv_edi_code": tax.tax_group_id.l10n_sv_edi_code,
                "l10n_sv_edi_tax_code": tax.l10n_sv_edi_tax_code,
                "l10n_sv_edi_tax_invoice_label": tax.invoice_label,
            }

        # def grouping_key_generator(base_line, tax_data):
        #     tax = tax_data['tax']
        #     return {
        #         'applied_tax_amount': tax.amount,
        #         'l10n_es_type': tax.l10n_es_type,
        #         'l10n_es_exempt_reason': tax.l10n_es_exempt_reason if tax.l10n_es_type == 'exento' else False,
        #         'l10n_es_bien_inversion': tax.l10n_es_bien_inversion,
        #     }

        values["tax_details"] = invoice._prepare_edi_tax_details()
        values["tax_details_grouped"] = invoice._prepare_edi_tax_details(grouping_key_generator=grouping_key_generator)
        for tax_key, tax_data in values["tax_details_grouped"]["tax_details"].items():
            tax_data["tax_amount_currency"] = clean_amount(tax_data["tax_amount_currency"], precision_rounding=precision_rounding)
            tax_data["base_amount_currency"] = clean_amount(tax_data["base_amount_currency"], precision_rounding=precision_rounding)
        return values

    # ------------------------------------------
    # Helpers
    # ------------------------------------------
    def _get_cod_estable(self, invoice):
        company = invoice.company_id.sudo()
        return {
            "codEstableMH": company.l10n_sv_edi_cod_estable_mh or None,
            "codEstable": company.l10n_sv_edi_cod_estable or None,
        }

    def clean_amount(self, value, precision_digits=None, precision_rounding=None):
        return (
            0.00 if float_is_zero(value, precision_digits, precision_rounding) else float_round(value, precision_digits, precision_rounding)
        )
