from odoo import api, models
from odoo.tools import float_round


class CcfDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.ccf"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Comprobante de Credito Fiscal Electrónico"

    name = "fe-ccf"
    _version = 3
    _tipoDte = "03"

    @api.model
    def generate_json(self, invoice, credentials):
        values = self._l10n_sv_edi_get_dte_values(invoice)
        return {
            "identificacion": self._get_identificacion(invoice, credentials),
            "documentoRelacionado": self._get_documento_relacionado(invoice),
            "emisor": self._get_emisor(invoice),
            "receptor": self._get_receptor(invoice),
            "otrosDocumentos": None,
            "ventaTercero": None,
            "cuerpoDocumento": self._get_cuerpo_documento(values),
            "resumen": self._get_resumen(values),
            "extension": self._get_extension(invoice),
            "apendice": self._get_apendice(invoice),
        }

    def _get_resumen(self, values):
        res = super()._get_resumen(values)
        return {
            **res,
            "numPagoElectronico": None,
            "porcentajeDescuento": 0.00,
            "totalNoGravado": 0.00,
            "saldoFavor": 0.00,
            "totalPagar": float_round(values["record"].amount_total or 0.00, 6),
            "pagos": [
                {
                    "codigo": x["code"],
                    "montoPago": x["amount"],
                    "referencia": None,
                    "plazo": None,
                    "periodo": None,
                }
                for x in values["invoice_date_due_vals_list"]
            ],
        }

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_estable = self._get_cod_estable(invoice)
        return {
            **res,
            **cod_estable,
            "codPuntoVentaMH": "0001",
            "codPuntoVenta": "0001",
        }

    def _get_cuerpo_documento(self, values):
        cuerpo_documento = []
        for item in values["invoice_line_vals_list"]:
            common_line = self._get_cuerpo_documento_common_line(item)
            # Tributos
            tributos = None
            line = item.get("line", False)
            venta_no_suj = 0.00
            venta_exenta = 0.00
            precioUni = 0.00
            montoDescu = 0.00
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                if item["line"].id == move_line.id:
                    quantity = data["base_line"]["quantity"]
                    precioUni = item["price_total_unit"] / (1 - (data["base_line"]["discount"] / 100))
                    montoDescu = (precioUni * quantity) - item["price_total_unit"] * quantity
                    if data.get("tax_amount_currency", 0) > 0:
                        tributos = [d.get("l10n_sv_edi_tax_code", None) for d in data["tax_details"] if d.get("l10n_sv_edi_tax_code")]
                    for tax_key, tax_values in data["tax_details"].items():
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_NO_SUJ":
                            venta_no_suj += tax_values.get("base_amount_currency", 0.00)
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_EXEN":
                            venta_exenta += tax_values.get("base_amount_currency", 0.00)
            cuerpo_documento.append(
                {
                    **common_line,
                    # "precioUni": item["price_subtotal_unit"],
                    "precioUni": float_round(item["gross_price_total_unit"], 6),
                    "montoDescu": float_round(item["price_discount"], 6),
                    # "montoDescu": montoDescu,
                    "ventaNoSuj": float_round(venta_no_suj, 6),
                    "ventaExenta": float_round(venta_exenta, 6),
                    "ventaGravada": float_round(line.price_subtotal or 0.00, 6),
                    "tributos": tributos,
                    "psv": 0.00,
                    "noGravado": 0.00,
                }
            )
        return cuerpo_documento
