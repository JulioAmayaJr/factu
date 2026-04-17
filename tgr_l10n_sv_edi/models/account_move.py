import copy
from urllib.parse import quote_plus, urlencode
import uuid

from num2words import num2words
from odoo import _, api, fields, models
import base64
import json
from io import BytesIO

import logging

_logger = logging.getLogger(__name__)
try:
    import qrcode
except ImportError:
    qrcode = None
    _logger.error("Could not import library qrcode")

CAT_005_CONTINGENCIA = [
    ("1", "[1] No disponibilidad del sistema del MH"),
    ("2", "[2] No disponibilidad del sistema del emisor"),
    ("3", "[3] Falla en el suministro de internet del emisor"),
    ("4", "[4] Falla en el suministro de energia eléctrica del emisor"),
    ("5", "[5] Otro"),
]

CAT_007_TIPO_GENERACION = [("1", "Físico"), ("2", "Electrónico")]

CAT_024_TIPO_INVAlIDACION = [
    # ("1", "Error en la información del DTE a invalidar"),
    ("2", "Rescindir de la operación realizada"),
    # ("3", "Otro"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    move_is_dte = fields.Boolean(string="Es DTE", compute="_compute_is_dte")
    tgr_l10n_sv_edi_codigo_generacion = fields.Char(string="Código de Generación", size=36, copy=False)
    tgr_l10n_sv_edi_sello_recibido = fields.Char(string="Sello de recepción", size=40, copy=False)
    tgr_l10n_sv_edi_tipo_invalidacion = fields.Selection(selection=CAT_024_TIPO_INVAlIDACION, string="Tipo de Invalidación", copy=False)
    tgr_l10n_sv_edi_motivo_invalidacion = fields.Char(string="Motivo de Invalidación", copy=False)
    tgr_l10n_sv_edi_numero_control = fields.Char(
        string="Número de Control",
        copy=False,
        size=31,
        help="""
    """,
    )
    tgr_l10n_sv_edi_json_name = fields.Char(copy=False)
    tgr_l10n_sv_edi_json_binary = fields.Binary("DTE", readonly=True, copy=False)
    tgr_l10n_sv_edi_cancel_sello_recibido = fields.Char(string="Sello de recepción Anulación", size=40, copy=False)
    tgr_l10n_sv_edi_cancel_json_name = fields.Char(copy=False)
    tgr_l10n_sv_edi_cancel_json_binary = fields.Binary("Anulación DTE", readonly=True, copy=False)
    contingency_event = fields.Boolean("Evento de Contingencia", default=False, readonly=True)
    tgr_l10n_sv_edi_tipo_generacion = fields.Selection(
        selection=CAT_007_TIPO_GENERACION,
        string="Tipo de Generacion del documento relacionado",
        copy=False,
        help="Tipo de generación del documento tributario relacionado",
    )
    contingency_type = fields.Selection(
        CAT_005_CONTINGENCIA,
        "Tipo de Contingencia",
        help="Tipo de evento de contingencia CAT 005",
    )
    contingency_reason = fields.Char("Motivo de Contingencia")

    tgr_l10n_sv_edi_barcode_image = fields.Char(string="SV Barcode Image", compute="_compute_l10n_sv_edi_barcode_image")

    def _compute_l10n_sv_edi_barcode_image(self):
        for record in self:
            record.tgr_l10n_sv_edi_barcode_image = False
            if record.tgr_l10n_sv_edi_codigo_generacion:
                barcode_file = BytesIO()
                if qrcode is None:
                    return False
                extra_values = record._l10n_sv_edi_get_extra_report_values()
                qr_str = extra_values.get("qr_str")
                if not qr_str:
                    _logger.warning("No se encontró 'qr_str' en los valoles de extra_values")
                qr = qrcode.QRCode(version=1, box_size=4, border=2)
                qr.add_data(qr_str)
                qr.make(fit=True)
                qr_image = qr.make_image(fill_color="black", back_color="white")
                qr_image.save(barcode_file, format="PNG")
                data = barcode_file.getvalue()
                record.tgr_l10n_sv_edi_barcode_image = base64.b64encode(data)

    @api.depends("move_type", "company_id")
    def _compute_is_dte(self):
        for move in self:
            move.move_is_dte = False
            if move.country_code == "SV":
                if move.move_type in ["out_invoice", "out_refund"] and move.journal_id.l10n_latam_use_documents:
                    move.move_is_dte = True

    # ----------------------------------------------------------
    # Utils
    # ----------------------------------------------------------

    @api.model
    def l10n_sv_edi_numero_control_values(self):
        """
        | Campo                             |long |
        ------------------------------------|-----|
         1. Letras 'DTE'                    | 3   |
         2. Tipo de Documento - Cat-002     | 2   |
         3. Codigo Casa matriz              | 4   |
         4. Codigo Punto de Venta           | 4   |
         5. Correlativo                     | 15  |

         DTE-document_code-cod_estable_mh|cod_pos_mh-correlativo
        """
        self.ensure_one()

        correlantivo = self.name
        correlantivo = str(int(correlantivo.split("-")[-1])).zfill(15)

        # Valores base
        return {
            "document_code": self.l10n_latam_document_type_id.code,
            "cod_estable_mh": self.company_id.sudo().l10n_sv_edi_cod_estable_mh or "0000",
            "cod_pos_mh": "P001",
            "correlantivo": correlantivo,
        }

    @api.model
    def _tgr_l10n_sv_edi_compute_numero_control(self):
        self.ensure_one()
        nume_control_values = self.l10n_sv_edi_numero_control_values()
        self.tgr_l10n_sv_edi_numero_control = "DTE-%s-%s%s-%s" % (
            nume_control_values["document_code"],
            nume_control_values["cod_estable_mh"],
            nume_control_values["cod_pos_mh"],
            nume_control_values["correlantivo"],
        )

    @api.model
    def _l10n_sv_edi_amount_to_text(self):
        self.ensure_one()
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = int(round(amount_d * 100, 2))
        words = num2words(amount_i, lang="es")
        result = "%(words)s %(currency_name)s Y %(amount_d)02d/100 %(currency_subunit)s" % {
            "words": words,
            "amount_d": amount_d,
            "currency_name": _(self.currency_id.currency_unit_label),
            "currency_subunit": _(self.currency_id.currency_subunit_label),
        }
        return result.upper()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super()._get_last_sequence_domain(relaxed=relaxed)
        if self.move_is_dte:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param["l10n_latam_document_type_id"] = self.l10n_latam_document_type_id.id or 0
        return where_string, param

    def _get_starting_sequence(self):
        if self.move_is_dte and self.l10n_latam_document_type_id:
            doc_mapping = {
                "01": "FE",  # Factura",
                "03": "CCFE",  # Comprobante crédito fiscal
                "04": "NRE",  # Nota de remisión
                "05": "NCE",  # Nota de crédito
                "06": "NDE",  # Nota de debito
                "07": "CRE",  # Comprobante de retención
                "08": "CLE",  # Comprobante de liquidación
                "09": "DCLE",  # Documento contable de liquidación
                "11": "FEXE",  # Factura de exportación
                "14": "FSEE",  # Factura de sujeto excluido
                "15": "CDE",  # Comprobante de donación
            }
            code = doc_mapping.get(self.l10n_latam_document_type_id.code)
            if self.journal_id.code != "INV":
                code = self.journal_id.code[:2] + "-" + code
            return f"{code}-000000"
        return super()._get_starting_sequence()

    def _get_json_identificacion(self):
        # Genera codigo de Generacion
        self.ensure_one()
        if not self.tgr_l10n_sv_edi_codigo_generacion:
            self.tgr_l10n_sv_edi_codigo_generacion = str(uuid.uuid4()).upper()

    # ----------------------------------------------------------
    # OVERRIDE
    # ----------------------------------------------------------
    def _post(self, soft=True):
        res = super()._post(soft)
        for move in self:
            if move.move_type in ["out_invoice", "out_refund"]:
                move._tgr_l10n_sv_edi_compute_numero_control()
                if not move.tgr_l10n_sv_edi_codigo_generacion:
                    move._get_json_identificacion()
        return res

    # ----------------------------------------------------------
    # BUSINESS METHODS
    # ----------------------------------------------------------

    def button_cancel_posted_moves(self):
        # OVERRIDE
        sv_edi_format = self.env.ref("tgr_l10n_sv_edi.edi_sv_dte_1", raise_if_not_found=False)
        sv_invoices = sv_edi_format and self.filtered(sv_edi_format._get_move_applicability)
        cancel_reason_needed = sv_invoices.filtered(lambda move: not move.tgr_l10n_sv_edi_tipo_invalidacion)
        if cancel_reason_needed:
            return self.env.ref("tgr_l10n_sv_edi.action_tgr_l10n_sv_edi_cancel").sudo().read()[0]
        return super().button_cancel_posted_moves()

    # --------------------------------------------------------tgr_l10n_sv_edi_motivo_invalidacion
    # REFORT
    # --------------------------------------------------------tgr_l10n_sv_edi_motivo_invalidacion
    def _l10n_sv_edi_get_extra_report_values(self):
        self.ensure_one()
        if not self.move_is_dte:
            return {}
        res = {
            "codigoGeneracion": self.tgr_l10n_sv_edi_codigo_generacion or False,
            "selloRecibido": self.tgr_l10n_sv_edi_sello_recibido or False,
            "numeroControl": self.tgr_l10n_sv_edi_numero_control or False,
            "totalLetras": self._l10n_sv_edi_amount_to_text().replace("DOLLARS", "DÓLARES").replace("CENTS", "CENTAVOS") or False,
        }
        if not self.tgr_l10n_sv_edi_json_binary:
            return res
        json_data = base64.b64decode(self.tgr_l10n_sv_edi_json_binary)
        json_dict = json.loads(json_data)
        res["version"] = json_dict["identificacion"].get("version")
        res["horEmi"] = json_dict["identificacion"].get("horEmi")
        base_url = "https://admin.factura.gob.sv/consultaPublica"
        params = {
            "ambiente": json_dict["identificacion"].get("ambiente", ""),
            "codGen": json_dict["identificacion"].get("codigoGeneracion", ""),
            "fechaEmi": json_dict["identificacion"].get("fecEmi", ""),
        }
        encoded_url = f"{base_url}?{urlencode(params)}"
        res["qr_str"] = encoded_url
        # res["qr_str"] = "https://admin.factura.gob.sv/consultaPublica?ambiente=%s&codGen=%s&fechaEmi=%s" % (
        #     json_dict["identificacion"].get("ambiente"),
        #     json_dict["identificacion"].get("codigoGeneracion"),
        #     json_dict["identificacion"].get("fecEmi"),
        # )
        if json_dict.get("documentoRelacionado"):
            res["documentoRelacionado"] = json_dict.get("documentoRelacionado")
        print("extra_report_values", res)
        return res
