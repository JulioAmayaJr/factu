from odoo import api, models
from odoo.tools import float_round


class FseDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.fse"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Comprobante de Sujeto Excluido"

    name = "fe-fse"
    _version = 1
    _tipoDte = "14"

    @api.model
    def generate_json(self, invoice, credentials):
        values = self._l10n_sv_edi_get_dte_values(invoice)
        return {
            "identificacion": self._get_identificacion(invoice, credentials),
            "emisor": self._get_emisor(invoice),
            "sujetoExcluido": self._get_receptor(invoice),
            "cuerpoDocumento": self._get_cuerpo_documento(values),
            "resumen": self._get_resumen(values),
            "apendice": None,
        }

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_estable = self._get_cod_estable(invoice)
        res = {k: v for k, v in res.items() if k not in ["nombreComercial", "tipoEstablecimiento"]}  # keys remove
        return {
            **res,
            **cod_estable,
            "codPuntoVentaMH": "0001",
            "codPuntoVenta": "0001",
        }

    def _get_receptor(self, invoice):
        res = super()._get_receptor(invoice)
        res = {k: v for k, v in res.items() if k not in ["nit", "nombreComercial", "nrc"]}  # Keys remove
        partner = invoice.commercial_partner_id
        return {
            **res,
            "tipoDocumento": (
                partner.l10n_latam_identification_type_id.l10n_sv_vat_code
                if partner.l10n_latam_identification_type_id and partner.vat
                else None
            ),
            "numDocumento": partner.vat or None,
        }

    def _get_cuerpo_documento(self, values):
        cuerpo_documento = []
        for item in values["invoice_line_vals_list"]:
            common_line = self._get_cuerpo_documento_common_line(item)
            common_line = {k: v for k, v in common_line.items() if k not in ["numeroDocumento", "codTributo"]}  # Keys remove
            compra = 0.0
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                if item["line"].id == move_line.id:
                    compra = data["base_amount_currency"]
            cuerpo_documento.append(
                {
                    **common_line,
                    "precioUni": float_round(item["gross_price_total_unit"], 6),
                    "montoDescu": float_round(item["price_discount"], 6),
                    "compra": float_round(compra, 6),
                }
            )
        return cuerpo_documento

    def _get_resumen(self, values):
        res = super()._get_resumen(values)
        totalDescu = 0.0
        subTotal = 0.0
        for item in values["invoice_line_vals_list"]:
            totalDescu += item["price_discount"]
        for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
            subTotal += data["base_amount_currency"]
        res = {
            k: v
            for k, v in res.items()
            if k
            not in [
                "totalNoSuj",
                "ivaPerci1",
                "descuNoSuj",
                "subTotalVentas",
                "tributos",
                "descuExenta",
                "descuGravada",
                "totalGravada",
                "montoTotalOperacion",
                "totalExenta",
            ]  # Keys remove
        }
        return {
            **res,
            "totalCompra": float_round(values["record"].amount_total or 0.0, 6),
            "descu": 0.0,  # Global discounts - not applicable to odoo
            "totalDescu": float_round(totalDescu, 6),  # Sum of discounts per line
            "subTotal": float_round(subTotal, 6),
            "observaciones": None,
            "totalPagar": float_round(values["record"].amount_total or 0.0, 6),
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
