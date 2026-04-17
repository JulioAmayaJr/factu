import json
import os
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from odoo import models
from odoo.tools import config, float_is_zero, float_round

TIPO_DTE_MAPPING = {
    "01": "01",  # Factura
    "03": "03",  # Crédito Fiscal
    "06": "06",  # Nota de Débito
    "11": "11",  # Factura de Exportación
    "14": "14",  # Factura Sujeto Excluido
}

CAT_11_MAPPING = {"consu": 1, "product": 1, "service": 2}

TAX_GROUP = {
    "IVA": 0,
    "IVA RETENIDO": 0,
    "EXENTO": 0,
    "NO SUJETA": 0,
    "IVA PERCIBIDO": 0,
    "IVA EXPORTACIÓN": 0,
    "IVA IMPORTACIÓN": 0,
}


class AccountEdiJsonDTESV(models.AbstractModel):
    # _inherit= 'account.edi.xml.ubl_20'
    _name = "account.edi.json.dte_sv"
    _description = "Generador de JSON para DTE en El Salvador"

    def _round(self, ammount, decimal=2):
        return float(Decimal(ammount).quantize(Decimal("0.01"), ROUND_HALF_UP))

    def _export_invoice_filename(self, invoice):
        return f"{invoice.name.replace('/', '_')}_ubl_sv.json"

    def _get_invoice_line_tax_totals_vals_list(self, taxes_vals):
        """Genera los totales de impuestos para una línea de factura"""
        tax_subtotals = []

        for tax_detail in taxes_vals["tax_details"].values():
            tax_id = tax_detail["group_tax_details"][0]["id"]
            tax = self.env["account.tax"].browse(tax_id)

            tax_subtotals.append(
                {
                    "taxable_amount": tax_detail["base_amount_currency"],
                    "tax_amount": tax_detail["tax_amount_currency"] or 0.0,
                    "tax_category_vals": {
                        "id": tax.l10n_sv_edi_tax_code,
                        "name": tax.tax_group_id.l10n_sv_edi_code,
                    },
                }
            )

        return [{"tax_subtotal_vals": tax_subtotals}]

    def _get_invoice_line_price_vals(self, line):
        vals = super()._get_invoice_line_price_vals(line)
        vals["price_amount"] = (
            float(Decimal(line.price_subtotal / line.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            if line.quantity
            else 0.0
        )
        return vals

    def _get_invoice_monetary_total_vals(
        self,
        invoice,
        taxes_vals,
        line_extension_amount,
        allowance_total_amount,
        charge_total_amount,
    ):
        vals = super()._get_invoice_monetary_total_vals(
            invoice,
            taxes_vals,
            line_extension_amount,
            allowance_total_amount,
            charge_total_amount,
        )
        if invoice.move_type == "out_refund":
            vals["payable_amount"] += vals["prepaid_amount"]
            vals["prepaid_amount"] = 0.0
        return vals

    def _get_tax_group_total_line(self, line):
        taxes_res = None
        l10n_sv_edi_code_totals = {
            "IVA_RETE": 0.00,
            "IVA": 0.00,
            "IVA_EXEN": 0.00,
            "IVA_NO_SUJ": 0.00,
            "IVA_PER": 0.00,
            "IVA_EXPO": 0.00,
            "IVA_IMPO": 0.00,
            "iva_item": 0.00,
        }
        line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
        if line.tax_ids:
            taxes_res = line.tax_ids.compute_all(
                line_discount_price_unit,
                quantity=line.quantity,
                currency=line.currency_id,
                product=line.product_id,
                partner=line.partner_id,
                is_refund=line.is_refund,
            )

            for tax in line.tax_ids:
                tax_group = tax.tax_group_id.l10n_sv_edi_code
                tax_amount = tax_amount = taxes_res["total_included"]
                if tax_group in l10n_sv_edi_code_totals:
                    l10n_sv_edi_code_totals[tax_group] += round(tax_amount, 8)
                if tax_group == "IVA":
                    l10n_sv_edi_code_totals["iva_item"] += round(sum(t["amount"] for t in taxes_res.get("taxes", [])), 8)
        return l10n_sv_edi_code_totals

    def _get_common_line_vals(self, values):
        cuerpo_documento = []
        for line in values["invoice_line_vals_list"]:
            # Tributos
            tributos = None
            venta_no_suj = 0.00
            venta_exenta = 0.00
            for move_line, data in values["tax_details_grouped"]["tax_details_per_record"].items():
                if line["line"].id == move_line.id:
                    if data.get("tax_amount_currency", 0) > 0:
                        tributos = [d.get("l10n_sv_edi_tax_code", None) for d in data["tax_details"]]
                    for tax_key, tax_values in data["tax_details"].items():
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_NO_SUJ":
                            venta_no_suj += tax_values.get("base_amount_currency", 0.00)
                        if tax_key.get("l10n_sv_edi_code", None) == "IVA_EXEN":
                            venta_exenta += tax_values.get("base_amount_currency", 0.00)
            cuerpo_documento.append(
                {
                    "numItem": line["index"],
                    "tipoItem": CAT_11_MAPPING.get(line["line"].product_id.product_tmpl_id.type, 1),
                    "cantidad": line["line"].quantity,
                    "codigo": line["line"].product_id.default_code or None,
                    "codTributo": None,  # Ajustar según configuración de tributos
                    "uniMedida": (
                        99
                        if line["line"].product_id.product_tmpl_id.type == "service"
                        else (line["line"].product_id.product_tmpl_id.uom_id.l10n_sv_edi_measure_unit_code or 99)
                    ),
                    "descripcion": line["line"].name or "",
                    "precioUni": line["price_subtotal_unit"],
                    "montoDescu": line["price_discount"],
                    "ventaNoSuj": venta_no_suj,
                    "ventaExenta": venta_exenta,  # tax_groups_totals["IVA_EXEN"],
                    "ventaGravada": line["line"].price_subtotal or 0.00,
                    "noGravado": 0.00,  # Ajustar según impuestos específicos
                    # "ivaItem": tax_groups_totals["iva_item"],
                    "psv": 0.00,
                    "tributos": tributos,  # Null solo FE
                    "numeroDocumento": None,  # Ajustar si aplica
                }
            )
        # for index, line in enumerate(invoice.invoice_line_ids, start=1):
        #     # Cálculo correcto del precio unitario
        #     if any(tax.price_include for tax in line.tax_ids):
        #         taxes_res = line.tax_ids.compute_all(
        #             line.price_unit,
        #             quantity=1,
        #             currency=line.currency_id,
        #             product=line.product_id,
        #             partner=line.partner_id,
        #             is_refund=line.is_refund,
        #         )
        #         print(taxes_res)
        #         precio_unitario = round(taxes_res["total_excluded"], 8)
        #     else:
        #         precio_unitario = round(line.price_unit, 8)
        #     tax_groups_totals = self._get_tax_group_total_line(line)
        #     cuerpo_documento.append(
        #         {
        #             "numItem": index,
        #             "tipoItem": CAT_11_MAPPING.get(line.product_id.product_tmpl_id.type, 1),
        #             "cantidad": line.quantity,
        #             "codigo": line.product_id.default_code or None,
        #             "codTributo": None,  # Ajustar según configuración de tributos
        #             "uniMedida": (
        #                 99
        #                 if line.product_id.product_tmpl_id.detailed_type == "service"
        #                 else (line.product_id.product_tmpl_id.uom_id.l10n_sv_edi_measure_unit_code or 99)
        #             ),
        #             "descripcion": line.name or "",
        #             "precioUni": precio_unitario,
        #             "montoDescu": (round((line.price_unit * line.quantity) * (line.discount / 100), 2) if line.discount else 0.00),
        #             "ventaNoSuj": tax_groups_totals["IVA_NO_SUJ"],
        #             "ventaExenta": tax_groups_totals["IVA_EXEN"],
        #             "ventaGravada": tax_groups_totals["IVA"],
        #             "noGravado": 0.00,  # Ajustar según impuestos específicos
        #             "ivaItem": tax_groups_totals["iva_item"],
        #             "psv": 0.00,
        #             "tributos": None,  # Null solo FE
        #             "numeroDocumento": None,  # Ajustar si aplica
        #         }
        #     )
        return cuerpo_documento

    def _get_common_resumen_vals(self, values):
        total_no_suj = 0.00
        total_exenta = 0.00
        total_gravada = 0.00
        sub_total_ventas = 0.00
        sub_total = 0.00
        tributos = []
        for tax_key, tax_data in values["tax_details_grouped"]["tax_details"].items():
            if tax_key["l10n_sv_edi_code"] == "IVA":
                total_gravada += tax_data["base_amount_currency"]
            tributos.append(
                {
                    "codigo": tax_key["l10n_sv_edi_tax_code"],
                    "descripcion": tax_key["l10n_sv_edi_tax_invoice_label"],
                    "valor": tax_data["tax_amount_currency"],
                }
            )
        sub_total_ventas = values["tax_details_grouped"]["base_amount_currency"] or 0.00
        sub_total = sub_total_ventas

        return {
            "totalNoSuj": total_no_suj,  # l10n_sv_edi_code_totals["IVA_NO_SUJ"],
            "totalExenta": total_exenta,  # l10n_sv_edi_code_totals["IVA_EXEN"],
            "totalGravada": total_gravada,  # l10n_sv_edi_code_totals["IVA"],
            "subTotalVentas": sub_total_ventas,  # sum(l10n_sv_edi_code_totals.values()),
            "descuNoSuj": 0.0,
            "descuExenta": 0.0,
            "descuGravada": 0.0,
            "porcentajeDescuento": 0.0,
            "totalDescu": 0.00,
            "tributos": tributos,
            "subTotal": sub_total,
            "ivaPerci1": 0.00,
            "ivaRete1": 0.0,
            "reteRenta": 0.0,
            "montoTotalOperacion": values["record"].amount_total or 0.00,
            "totalNoGravado": 0.00,
            "totalPagar": values["record"].amount_total or 0.00,
            "totalLetras": str(values["record"]._l10n_sv_edi_amount_to_text()).replace("DOLLARS", "DÓLARES").replace("CENTS", "CENTAVOS"),
            # "totalIva": totalIva,
            "saldoFavor": 0.0,
            "condicionOperacion": 1,
            "pagos": [
                {"codigo": x["code"], "montoPago": x["amount"], "referencia": None, "plazo": None, "periodo": None}
                for x in values["invoice_date_due_vals_list"]
            ],  # Ajustar si hay datos de pagos
            # "tributos": None,
            "numPagoElectronico": None,
        }

    def _get_common_direccion(self, partner_id):

        if not partner_id.state_id or not partner_id.city_id or not partner_id.street:
            return None
        return {
            "departamento": partner_id.state_id.code or None,
            "municipio": partner_id.city_id.l10n_sv_code or None,
            "complemento": partner_id.street or None,
        }

    def _get_common_vals(self, invoice, credentials):
        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.commercial_partner_id
        values = self._l10n_sv_edi_get_dte_values(invoice)
        documentoRelacionado = None
        ventaTercero = None
        otrosDocumentos = None
        extension = None
        apendice = None
        identificacion = {
            "version": 3,
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "tipoDte": invoice.l10n_latam_document_type_id.code or "00",
            "numeroControl": invoice.tgr_l10n_sv_edi_numero_control or "",
            "codigoGeneracion": invoice.tgr_l10n_sv_edi_codigo_generacion or "",
            "tipoModelo": 1,
            "tipoOperacion": 2 if invoice.contingency_event else 1,
            "tipoContingencia": (int(invoice.contingency_type) if invoice.contingency_event else None),
            "motivoContin": (invoice.contingency_reason if invoice.contingency_event else None),
            "fecEmi": invoice.date.strftime("%Y-%m-%d"),
            "horEmi": datetime.now(ZoneInfo("America/El_Salvador")).strftime("%H:%M:%S"),
            "tipoMoneda": invoice.currency_id.name,
        }
        emisor = {
            "nit": supplier.vat or "",
            "nrc": supplier.l10n_sv_nrc or "",
            "correo": supplier.email or None,
            "nombre": supplier.display_name or "",
            "telefono": supplier.phone or None,
            "direccion": self._get_common_direccion(supplier),
            "codEstable": None,
            "codActividad": supplier.l10n_sv_edi_economic_activity_id.code or None,
            "codEstableMH": None,
            "codPuntoVenta": None,
            "descActividad": supplier.l10n_sv_edi_economic_activity_id.name or None,
            "codPuntoVentaMH": None,
            "nombreComercial": supplier.display_name or "",
            "tipoEstablecimiento": "01",
        }
        receptor = {
            "nit": customer.vat or "",
            "nrc": customer.l10n_sv_nrc or None,
            "nombre": customer.display_name or "",
            "nombreComercial": customer.display_name or " ",
            "codActividad": customer.l10n_sv_edi_economic_activity_id.code or None,
            "descActividad": customer.l10n_sv_edi_economic_activity_id.name or None,
            "direccion": self._get_common_direccion(customer),
            "telefono": customer.phone or None,
            "correo": customer.email or None,
        }
        return {
            "otrosDocumentos": otrosDocumentos,
            "documentoRelacionado": documentoRelacionado,
            "ventaTercero": ventaTercero,
            "extension": extension,
            "identificacion": identificacion,
            "emisor": emisor,
            "receptor": receptor,
            "cuerpoDocumento": self._get_common_line_vals(values),
            "resumen": self._get_common_resumen_vals(values),
            "apendice": apendice,
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
        for index, rec_line in enumerate(invoice.line_ids.filtered(lambda l: l.account_type == "asset_receivable"), start=1):
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
        }
        # Invoice lines
        for line_vals in values["invoice_line_vals_list"]:
            line = line_vals["line"]
            line_vals["price_subtotal_unit"] = (
                clean_amount(line.price_subtotal / line.quantity, precision_rounding=precision_rounding) if line.quantity else 0.00
            )
            line_vals["price_total_unit"] = (
                clean_amount(line.price_total / line.quantity, precision_rounding=precision_rounding) if line.quantity else 0.00
            )
            line_vals["price_discount"] = clean_amount(line_vals["price_discount"], precision_rounding=precision_rounding)
            line_vals["price_discount_unit"] = clean_amount(line_vals["price_discount_unit"], precision_rounding=precision_rounding)

        # Tax Details
        def grouping_key_generator(base_line, tax_values):
            tax = tax_values["tax_repartition_line"].tax_id
            return {
                "l10n_sv_edi_code": tax.tax_group_id.l10n_sv_edi_code,
                "l10n_sv_edi_tax_code": tax.l10n_sv_edi_tax_code,
                "l10n_sv_edi_tax_invoice_label": tax.invoice_label,
            }

        values["tax_details"] = invoice._prepare_edi_tax_details()
        values["tax_details_grouped"] = invoice._prepare_edi_tax_details(grouping_key_generator=grouping_key_generator)
        for tax_key, tax_data in values["tax_details_grouped"]["tax_details"].items():
            tax_data["tax_amount_currency"] = clean_amount(tax_data["tax_amount_currency"], precision_rounding=precision_rounding)
            tax_data["base_amount_currency"] = clean_amount(tax_data["base_amount_currency"], precision_rounding=precision_rounding)
        return values

    def _export_invoice_vals(self, invoice, credentials):
        vals = self._get_common_vals(invoice, credentials)
        print(json.dumps(vals, indent=2, ensure_ascii=False))
        self._validate_json(vals, "fe-ccf-v3")
        return vals

    def _validate_json(self, json_data, schema_name):
        def _load_scheme(schema_name):

            # module_path = os.path.dirname(os.path.abspath(__file__))
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            file_path = "%s/data/svfe-json-schemas/%s.json" % (module_path, schema_name)
            try:
                with open(file_path, "r") as file:
                    return json.load(file)
            except Exception as e:
                print("Error en cargar el schema: %s \n %s" % (file_path, str(e)))

        try:
            validate(instance=json_data, schema=_load_scheme(schema_name))
            print("El json es valido segun el schema")
        except ValidationError as e:
            print(f"Error de validación en '{'.'.join(map(str, e.path))}': {e.message}")
        except SchemaError as e:
            print(f"Error de validación en '{'.'.join(map(str, e.path))}': {e.message}")
        except Exception as e:
            print("Error de inesperado : %s" % (e))
