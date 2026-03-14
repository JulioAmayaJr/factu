from odoo import api, models
from odoo.tools import float_round


class NdDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.nd"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Nota de Debito Electrónica"

    name = "fe-nd"
    _version = 3
    _tipoDte = "06"

    @api.model
    def generate_json(self, invoice, credentials):
        values = self._l10n_sv_edi_get_dte_values(invoice)
        doc_rel_cod_generacion = invoice.debit_origin_id.tgr_l10n_sv_edi_codigo_generacion
        return {
            "identificacion": self._get_identificacion(invoice, credentials),
            "documentoRelacionado": self._get_documento_relacionado(invoice, doc_rel_cod_generacion),
            "emisor": self._get_emisor(invoice),
            "receptor": self._get_receptor(invoice),
            "ventaTercero": None,
            "cuerpoDocumento": self._get_cuerpo_documento(values=values, codigo_generacion=doc_rel_cod_generacion),
            "resumen": self._get_resumen(values),
            "extension": None,
            "apendice": None,
        }

    @api.model
    def _get_documento_relacionado(self, invoice, numero_control):
        return [
            {
                "tipoDocumento": invoice.debit_origin_id.l10n_latam_document_type_id.code,
                "tipoGeneracion": int(invoice.tgr_l10n_sv_edi_tipo_generacion) or 2,
                "numeroDocumento": numero_control,
                "fechaEmision": invoice.debit_origin_id.invoice_date.strftime("%Y-%m-%d"),
            }
        ]

    def _get_cuerpo_documento(self, values, codigo_generacion):
        cuerpo_documento = []
        for item in values["invoice_line_vals_list"]:
            common_line = self._get_cuerpo_documento_common_line(item)
            common_line["numeroDocumento"] = codigo_generacion
            # Tributos
            tributos = None
            line = item.get("line", False)
            venta_no_suj = 0.00
            venta_exenta = 0.00
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                if item["line"].id == move_line.id:
                    if data.get("tax_amount_currency", 0) > 0:
                        tributos = [d.get("l10n_sv_edi_tax_code", None) for d in data["tax_details"]]
                    for tax_key, tax_values in data["tax_details"].items():
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_NO_SUJ":
                            venta_no_suj += tax_values.get("base_amount_currency", 0.00)
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_EXEN":
                            venta_exenta += tax_values.get("base_amount_currency", 0.00)

            cuerpo_documento.append(
                {
                    **common_line,
                    "precioUni": float_round(item["gross_price_total_unit"], 6),
                    "montoDescu": float_round(item["price_discount"], 6),
                    "ventaNoSuj": float_round(venta_no_suj, 6),
                    "ventaExenta": float_round(venta_exenta, 6),
                    "ventaGravada": float_round(line.price_subtotal or 0.00, 6),
                    "tributos": tributos,
                }
            )
        return cuerpo_documento

    def _get_resumen(self, values):
        res = super()._get_resumen(values)
        return {
            **res,
            "numPagoElectronico": "",
        }
