from odoo import api, models
from decimal import Decimal
import logging
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class CfDteDocument(models.AbstractModel):
    _name = "l10n_sv.dte.cf"
    _inherit = "l10n_sv.dte.mixin"
    _description = "Comprobante de Consumidor Final"

    name = "fe-fc"
    _version = 1
    _tipoDte = "01"

    @api.model
    def generate_json(self, invoice, credentials):
        values = self._l10n_sv_edi_get_dte_values(invoice)
        receptor = self._get_receptor(invoice)
        partner = invoice.commercial_partner_id
        # eliminar llave nit del diccionario receptor
        receptor.pop("nit", None)
        receptor.pop("nombreComercial", None)
        receptor["tipoDocumento"] = (
            partner.l10n_latam_identification_type_id.l10n_sv_vat_code
            if partner.l10n_latam_identification_type_id and partner.vat
            else None
        )
        receptor["numDocumento"] = partner.vat or None
        cuerpo_documento = self._get_cuerpo_documento(values)
        return {
            "identificacion": self._get_identificacion(invoice, credentials),
            "documentoRelacionado": None,
            "emisor": self._get_emisor(invoice),
            "receptor": receptor,
            "otrosDocumentos": None,
            "ventaTercero": None,
            "cuerpoDocumento": cuerpo_documento,
            "resumen": self._get_resumen(values),
            "extension": None,
            "apendice": None,
        }

    def _get_emisor(self, invoice):
        res = super()._get_emisor(invoice)
        cod_estable = self._get_cod_estable(invoice)
        return {
            **res,
            **cod_estable,
            "codPuntoVentaMH": "P001",
            "codPuntoVenta": "0001",
        }

    @api.model
    def _get_cuerpo_documento(self, values):
        cuerpo_documento = []
        for item in values["invoice_line_vals_list"]:
            """
            quantity= 10
            price = 1
            tax: 13%
            discount = 10%
            item {
                'line': account.move.line(115,),
                'price_unit_after_discount': 0.9,
                'price_subtotal_before_discount': 10.0,
                'price_subtotal_unit': 0.9,
                'price_total_unit': 1.017,
                'price_discount': 1.0,
                'price_discount_unit': 0.1,
                'gross_price_total_unit': 1.0,
                'unece_uom_code': 'C62',
                'index': 1}
            """
            common_line = self._get_cuerpo_documento_common_line(item)
            ivaItem = 0.00
            ventaGravada = 0.00
            precioUni = 0.00
            montoDescu = 0.00
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                """
                quantity= 10
                price = 1
                tax: 13%
                discount = 10%

                data {
                    'base_amount_currency': 9.0,
                    'base_amount': 9.0,
                    'tax_amount_currency': 1.17,
                    'tax_amount': 1.17,
                    'base_line': {
                        'price_unit': 1.0,
                        'quantity': 10.0,
                        'discount': 10.0,
                        'rate': 1.0,
                        'sign': -1,
                        'special_mode': False,
                        'record': account.move.line(115,),
                        'id': 115,
                        'product_id': product.product(18,),
                        'tax_ids': account.tax(3,),
                        'currency_id': res.currency(1,),
                        'special_type': False,
                        'manual_tax_amounts': None,
                        'is_refund': False,
                        'tax_tag_invert': True,
                        'partner_id': res.partner(47,),
                        'account_id': account.account(157,),
                        'analytic_distribution': False,
                        'deferred_start_date': False,
                        'deferred_end_date': False,
                        'tax_details': {
                            'raw_total_excluded_currency': 9.0,
                            'raw_total_excluded': 9.0,
                            'raw_total_included_currency': 10.17,
                            'raw_total_included': 10.17,
                            'taxes_data': [
                                {
                                    'tax': account.tax(3,),
                                    'group': account.tax(),
                                    'batch': account.tax(3,),
                                    'tax_amount': 1.17,
                                    'base_amount': 9.0,
                                    'is_reverse_charge': False,
                                    'raw_tax_amount_currency': 1.17,
                                    'raw_tax_amount': 1.17,
                                    'raw_base_amount_currency': 9.0,
                                    'raw_base_amount': 9.0,
                                    'tax_amount_currency': 1.17,
                                    'base_amount_currency': 9.0}],
                                    'total_excluded_currency': 9.0,
                                    'total_excluded': 9.0,
                                    'delta_total_excluded_currency': 0.0,
                                    'delta_total_excluded': 0.0,
                                    'total_included_currency': 10.17,
                                    'total_included': 10.17
                                    }},
                                    'tax_details': {
                                        {
                                            'l10n_sv_edi_code': 'IVA',
                                            'l10n_sv_edi_tax_code': '20',
                                            'l10n_sv_edi_tax_invoice_label': '13% IVA'
                                        }: {
                                            'base_amount_currency': 9.0,
                                            'base_amount': 9.0,
                                            'raw_base_amount_currency': 9.0,
                                            'raw_base_amount': 9.0,
                                            'tax_amount_currency': 1.17,
                                            'tax_amount': 1.17,
                                            'raw_tax_amount_currency': 1.17,
                                            'raw_tax_amount': 1.17,
                                            'total_excluded_currency': 9.0,
                                            'total_excluded': 9.0,
                                            'taxes_data': [
                                                {'tax': account.tax(3,),
                                                'group': account.tax(),
                                                'batch': account.tax(3,),
                                                'tax_amount': 1.17,
                                                'base_amount': 9.0,
                                                'is_reverse_charge': False,
                                                'raw_tax_amount_currency': 1.17,
                                                'raw_tax_amount': 1.17,
                                                'raw_base_amount_currency': 9.0,
                                                'raw_base_amount': 9.0,
                                                'tax_amount_currency': 1.17,
                                                'base_amount_currency': 9.0}],
                                                'grouping_key': {
                                                    'l10n_sv_edi_code': 'IVA',
                                                    'l10n_sv_edi_tax_code': '20',
                                                    'l10n_sv_edi_tax_invoice_label': '13% IVA'
                                                    },
                                                    'l10n_sv_edi_code': 'IVA',
                                                    'l10n_sv_edi_tax_code': '20',
                                                    'l10n_sv_edi_tax_invoice_label':
                                                    '13% IVA'
                                                    }
                                                }
                                            }
                """
                if item["line"].id == move_line.id:
                    ventaGravada = sum(
                        v.get("raw_base_amount_currency") + v.get("raw_tax_amount_currency")
                        for v in data["tax_details"].values()
                        if v.get("l10n_sv_edi_code") not in ["IVA_RETE"]
                    )
                    ivaItem = sum(
                        v.get("raw_tax_amount_currency")
                        for v in data["tax_details"].values()
                        if v.get("l10n_sv_edi_code") not in ["IVA_RETE"]
                    )
                    quantity = data["base_line"]["quantity"]
                    # ventaGravada = round(item["price_total_unit"] * quantity, 6)
                    # precioUni = round((item["price_total_unit"] / (1 - (data["base_line"]["discount"] / 100))), 6)
                    precioUni = ventaGravada / quantity
                    # montoDescu = round((precioUni * quantity) - item["price_total_unit"] * quantity, 6)
                    montoDescu = ventaGravada * (data["base_line"]["discount"] / 100)
            cuerpo_documento.append(
                {
                    **common_line,
                    # "precioUni": round(item["price_total_unit"], 6),
                    "precioUni": float_round(precioUni, 2),
                    "montoDescu": float_round(montoDescu, 2),
                    "ventaNoSuj": 0.0,
                    "ventaExenta": 0.0,
                    # "ventaGravad": round(base_amount + tax_amount, 6),
                    "ventaGravada": float_round(ventaGravada, 2),
                    "tributos": None,
                    "psv": 0.0,
                    "noGravado": 0.0,
                    "ivaItem": float_round(ivaItem, 2),
                }
            )
        return cuerpo_documento

    @api.model
    def _get_resumen(self, values):
        total_no_suj = 0.00
        total_exenta = 0.00
        total_gravada = 0.00
        total_iva = 0.00
        total_venta = values["record"].amount_total or 0.00
        iva_rete1 = 0.00
        for tax_key, tax_data in values["tax_details_grouped"]["tax_details"].items():
            if tax_key["l10n_sv_edi_code"] == "IVA":
                total_gravada += tax_data["base_amount_currency"]
                total_iva += tax_data["tax_amount_currency"]
            if tax_key["l10n_sv_edi_code"] == "IVA_RETE":
                iva_rete1 += tax_data["tax_amount_currency"] * -1

        totalDescu = 0.00
        for item in values["invoice_line_vals_list"]:
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                if item["line"].id == move_line.id:
                    quantity = data["base_line"]["quantity"]
                    precioUni = item["price_total_unit"] / (1 - (data["base_line"]["discount"] / 100))
                    descuento = (precioUni * quantity) - (item["price_total_unit"] * quantity)
                    totalDescu += float(descuento)
        return {
            "totalNoSuj": float_round(total_no_suj, 2),
            "totalExenta": float_round(total_exenta,2),
            # "totalGravada": total_venta,
            "totalGravada": float_round(total_gravada + total_iva, 2),
            "subTotalVentas": float_round(total_gravada + total_iva, 2),
            "descuNoSuj": 0.0,
            "descuExenta": 0.0,
            "descuGravada": 0.0,
            "porcentajeDescuento": 0.0,
            "totalDescu": float(Decimal(str(totalDescu)).quantize((Decimal("0.01")))),
            "tributos": None,
            "subTotal": float_round(total_gravada + total_iva, 2),
            "ivaRete1": float_round(iva_rete1, 2),
            "reteRenta": 0.0,
            "montoTotalOperacion": float_round(total_venta + iva_rete1 or 0.00, 2),
            "totalNoGravado": 0.00,
            "totalPagar": float_round(total_venta, 2),
            "totalLetras": str(values["record"]._l10n_sv_edi_amount_to_text()).replace("DOLLARS", "DÓLARES").replace("CENTS", "CENTAVOS"),
            "totalIva": float_round(total_iva, 2),
            "saldoFavor": 0.00,
            "condicionOperacion": 1,
            "pagos": None,
            "numPagoElectronico": None,
        }
