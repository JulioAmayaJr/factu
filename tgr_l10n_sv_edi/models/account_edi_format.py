import base64
import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from json.decoder import JSONDecodeError
from math import prod

import requests
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from odoo import models

_logger = logging.getLogger(__name__)
ERROR_MESSAGES = {
    "request": "Hubo un error al comunicarse con el servicio de Ministerio de Hacienda" + " " + "Detalles:",
    "json_decode": "No se pudo decodificar la respuesta recibida de Ministerio de Hacienda" + " " + "Detalles:",
    "response_code": "M.H. devolvió un código de error." + " " + "Detalles:",
    "response_unknown": "No se pudo identificar el contenido en la respuesta recuperada del M.H." + " " + "Detalles:",
}

I_VERSION_3 = ["01", "03", "04", "05", "06"]
I_T_MODELO_2 = ["01", "03", "04", "05", "06", "11", "14"]

url_electronic_sign = "http://firmaelectronicadte.tagre.pe:8222"
# url_electronic_sign = "http://5.161.197.115:8113"
# url_proxy = "http://proxydte.tagre.pe/"


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    # ----------------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------------

    def _round_decimals(self, number: float, num_decimals=2):
        # Round half up to num_decimals
        round_factor = Decimal("0." + "0" * num_decimals)
        _number = Decimal(number).quantize(round_factor, ROUND_HALF_UP)
        return float(_number)

    def _get_dte_credentials(self, invoice):
        root_company = invoice.company_id.l10n_sv_edi_get_root_company()
        missing_fields = []

        # Verificar cada campo obligatorio
        if not root_company.l10n_sv_edi_cert_private_key and not root_company.l10n_sv_edi_certificate_id:
            missing_fields.append("🔑 Clave privada del certificado ó Certifcado en: %s" % (root_company.name))
        # if not company.l10n_sv_edi_cert_public_key:
        #     missing_fields.append("🔑 Clave pública del certificado")
        if not root_company.vat:
            missing_fields.append("🏢 NIT de la empresa en: %s" % (root_company.name))
        if not root_company.l10n_sv_edi_username:
            missing_fields.append("👤 Usuario de autenticación")
        if not root_company.l10n_sv_edi_password:
            missing_fields.append("🔒 Contraseña de autenticación")
        if not root_company.l10n_sv_edi_signer_url and not root_company.l10n_sv_edi_certificate_id:
            missing_fields.append("🌍 Url del firmador ó Certifcado)")
        if not root_company.l10n_sv_edi_proxy_url and root_company.l10n_sv_edi_communication_mode == "proxy":
            missing_fields.append("🌍 Url del servidor proxy)")

            # Si hay errores, devolverlos en una sola respuesta con formato HTML
        if missing_fields:
            error_message = Markup(
                "<strong>Faltan los siguientes campos de configuración:</strong><br/>"
                + "<ul>"
                + "".join(f"<li>{field}</li>" for field in missing_fields)
                + "</ul>"
            )
            return {"error": error_message}

            # Si no hay errores, devolver las credenciales
        environment = root_company.l10n_sv_edi_environment  # 'test' or 'prod'
        comu_mode = root_company.l10n_sv_edi_communication_mode  # 'direct' or 'proxy'
        api_urls = {
            "prod": {
                "direct": "https://api.dtes.mh.gob.sv/",
                "proxy": root_company.l10n_sv_edi_proxy_url or None,
            },
            "test": {
                "direct": "https://apitest.dtes.mh.gob.sv/",
                "proxy": "%s/test" % (root_company.l10n_sv_edi_proxy_url or None),
            },
        }

        credentials = {
            "vat": root_company.vat,
            "user": root_company.l10n_sv_edi_username,
            "password": root_company.l10n_sv_edi_password,
            "l10n_sv_edi_cert_private_key": root_company.l10n_sv_edi_cert_private_key,
            "l10n_sv_edi_cert_public_key": root_company.l10n_sv_edi_cert_public_key,
            "environment": environment,
            "signer_url": root_company.l10n_sv_edi_signer_url or False,
            "api_url": api_urls[environment][comu_mode],
            "certificate_id": root_company.l10n_sv_edi_certificate_id.id or False,
        }
        return credentials

    def _get_token(self, force_request=False, invoice=None):
        root_company = invoice.company_id.l10n_sv_edi_get_root_company()
        existing_token = root_company.l10n_sv_edi_token
        if not force_request and existing_token:
            return {"token": existing_token}

        credentials = self._get_dte_credentials(invoice)
        if "error" in credentials:
            return credentials
        res_request_token = self._request_token(credentials)
        if "error" in res_request_token:
            return res_request_token
        token = res_request_token["body"]["token"]
        root_company.write({"l10n_sv_edi_token": token})
        return {"token": token}

    def _request_token(self, credentials):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Tagre-dte-sv",
        }
        data = {"user": credentials["user"], "pwd": credentials["password"]}
        try:
            response = requests.post(
                url="%s/seguridad/auth" % credentials["api_url"],
                data=data,
                headers=headers,
                timeout=20,
            )
            _logger.info(response.url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["request"], e))}

        try:
            response_json = response.json()
        except JSONDecodeError as e:
            return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["json_decode"], e))}

        if response_json.get("status") == "ERROR":
            error_msg = str(
                Markup("%s<br/>%s: %s")
                % (
                    ERROR_MESSAGES["response_code"],
                    response_json["body"]["codigoMsg"],
                    response_json["body"]["descripcionMsg"],
                )
            )
            return {"error": error_msg}
        if not response_json.get("body")["token"]:
            return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["response_unknown"], response_json))}

        return response_json

    # ----------------------------------------------------------------------------
    # Electronic Invoice Methods
    # ----------------------------------------------------------------------------

    def _tgr_l10n_sv_edi_signs_invoice(self, invoice):
        logging.info("--------------_tgr_l10n_sv_edi_signs_invoice ---------------")
        credentials = self._get_dte_credentials(invoice)
        if credentials.get("error"):
            return {invoice: {"error": credentials["error"], "blocking_level": "error"}}
        tipo_dte = invoice.l10n_latam_document_type_id.code
        dte_model = None
        if tipo_dte == "03":
            dte_model = self.env["l10n_sv.dte.ccf"]
        elif tipo_dte == "01":
            dte_model = self.env["l10n_sv.dte.cf"]
        elif tipo_dte == "05":
            dte_model = self.env["l10n_sv.dte.nc"]
        elif tipo_dte == "06":
            dte_model = self.env["l10n_sv.dte.nd"]
        elif tipo_dte == "14":
            dte_model = self.env["l10n_sv.dte.fse"]
        else:
            return {
                invoice: {
                    "error": "Tipo de DTE No soportado:  %s" % (tipo_dte),
                    "blocking_level": "error",
                }
            }
        dte_json = dte_model.generate_json(invoice, credentials)
        json_string = json.dumps(dte_json, indent=2)
        _logger.warning(json_string)
        json_binary = base64.b64encode(json_string.encode("utf-8"))
        invoice.write(
            {
                "tgr_l10n_sv_edi_json_binary": json_binary,
                "tgr_l10n_sv_edi_json_name": "DTE_%s.json" % (invoice.name),
            }
        )

        # sign document
        dte_json_sign = self._tgr_l10n_sv_edi_sign_json(dte_json, credentials)

        if dte_json_sign.get("error"):
            return {invoice: {"error": dte_json_sign["error"], "blocking_level": "error"}}
        # send to api dte
        res = self._tgr_l10n_sv_edi_post_invoice_api_dte(
            dte_json=dte_json,
            dte_json_sing=dte_json_sign,
            codigoGeneracion=invoice.tgr_l10n_sv_edi_codigo_generacion,
            tipoDte=invoice.l10n_latam_document_type_id.code,
            invoice=invoice,
        )
        return {invoice: res}

        # debug
        # return {invoice: {"error": "error", "blocking_level": "error"}}
        # end debug

        # respuesta en caso se procese correctamente
        # return {invoice: {"success": True, "xml_document": "xml_document", "cdr": "cdr"}}
        # j

    def _tgr_l10n_sv_edi_sign_json(self, dte_json, credentials):
        # sign document
        def api_signer_json(dte):
            headers = {"Content-Type": "application/JSON"}

            data = {
                "nit": credentials.get("vat"),
                "activo": True,
                "passwordPri": credentials.get("l10n_sv_edi_cert_private_key"),
                "dteJson": dte,
            }
            try:
                response = requests.request(
                    "POST",
                    "%s/firmardocumento/" % credentials.get("signer_url"),
                    headers=headers,
                    json=data,
                    timeout=20,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["request"], e))}

            try:
                response_json = response.json()
            except JSONDecodeError as e:
                return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["json_decode"], e))}

            if response_json.get("status") == "ERROR":
                error_msg = "Codigo: %s <br/> Mensajes: %s" % (
                    response_json.get("body")["codigo"],
                    "".join(response_json.get("body")["mensaje"]),
                )
                return {"error": error_msg}

            return response_json

        def signner_json(dte):
            signer = self.env["l10n_sv.certificate"].browse(int(credentials["certificate_id"]))
            return signer.signer_dte(dte)

        if credentials["signer_url"] and not credentials["certificate_id"]:
            json_sign = api_signer_json(dte_json)
            _logger.info("Firma del DTE desde %s" % credentials["signer_url"])
        else:
            json_sign = signner_json(dte_json)
            _logger.info("Firma del DTE desde odoo")
        return json_sign

    def _tgr_l10n_sv_edi_post_invoice_api_dte(
        self,
        dte_json,
        dte_json_sing,
        tipoDte,
        codigoGeneracion,
        invoice,
        force_request=False,
    ):
        token = self._get_token(force_request=force_request, invoice=invoice)
        if token.get("error", False):
            return token
        credentials = self._get_dte_credentials(invoice)
        if credentials.get("error", False):
            return credentials

        payload = {
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "idEnvio": 1,
            "version": dte_json["identificacion"]["version"],
            "tipoDte": tipoDte,
            "documento": dte_json_sing["body"],
            "codigoGeneracion": codigoGeneracion,
        }
        headers = {
            "User-Agent": "Tagre-dte-sv",
            "Content-Type": "application/JSON",
            "Authorization": token["token"],
        }

        try:
            response = requests.request(
                "POST",
                "%s/recepciondte" % credentials["api_url"],
                headers=headers,
                json=payload,
                verify=True,
                timeout=60,
            )
        except requests.exceptions.RequestException as e:
            return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["request"], e))}

        if response.status_code == 401:  # Unauthorized
            # Intentar nuevamente con force_request=True
            _logger.warning("Reintentatdo con force_request=True para forzar la obtencion de nuevo token")
            return self._tgr_l10n_sv_edi_post_invoice_api_dte(
                dte_json=dte_json,
                dte_json_sing=dte_json_sing,
                codigoGeneracion=codigoGeneracion,
                tipoDte=tipoDte,
                invoice=invoice,
                force_request=True,
            )
        if response.status_code == 403:
            return {
                "error": str(
                    Markup("%s<br/>%s<br/>%s")
                    % (
                        ERROR_MESSAGES["request"],
                        "403 Forbidden",
                        "Posible restricción GEO-IP del M.H., intentar la conexión mediante un proxy",
                    )
                )
            }
        if response.status_code == 404:
            return {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["request"], "404 Not Found"))}
        try:
            response_json = response.json()
        except JSONDecodeError as e:
            return {"error": str(Markup("%s<br/>%s<br/>%s") % (ERROR_MESSAGES["json_decode"], e, response.text))}

        if response_json.get("codigoMsg") not in ["001", "002"] or response.status_code != 200:
            error_msg = str(Markup("%s<br/>: %s") % (ERROR_MESSAGES["response_code"], response_json))
            return {"error": error_msg}
        _logger.info("DTE Procesado")
        # Chatter.
        json_document = dte_json
        json_document["firmaElectronica"] = dte_json_sing["body"]
        json_document["selloRecibido"] = response_json.get("selloRecibido")
        res = {"success": True, "xml_document": json_document}
        if json_document:
            json_data = json.dumps(json_document, indent=2, ensure_ascii=False)
            json_data_base64 = base64.b64encode(json_data.encode("utf-8"))
            res["attachment"] = self.env["ir.attachment"].create(
                {
                    "res_model": invoice._name,
                    "res_id": invoice.id,
                    "type": "binary",
                    "name": "%s.json" % codigoGeneracion,
                    "datas": json_data_base64,
                    "mimetype": "application/json",
                }
            )
            invoice.write(
                {
                    "tgr_l10n_sv_edi_sello_recibido": response_json.get("selloRecibido", False),
                    "tgr_l10n_sv_edi_json_binary": json_data_base64,
                    "tgr_l10n_sv_edi_json_name": "%s.json" % (response_json.get("selloRecibido", invoice.name)),
                }
            )
            observaciones = "<br/>".join(response_json["observaciones"]) if response_json["observaciones"] else "No hay observaciones"
            message = (
                "Estado del Documento Electrónico Estado: %s, Codigo de generacion: %s,  Sello recibido: %s, Fecha de Procesamiento: %s, Codigo de mensaje: %s, Descripcion: %s, Observaciones: %s"
                % (
                    response_json.get("estado", "N/A"),
                    response_json.get("codigoGeneracion", "N/A"),
                    response_json.get("selloRecibido", "N/A"),
                    response_json.get("fhProcesamiento", "N/A"),
                    response_json.get("codigoMsg", "N/A"),
                    response_json.get("descripcionMsg", "N/A"),
                    observaciones,
                )
            )

            invoice.with_context(no_new_invoice=True).message_post(
                body=message,
                attachment_ids=res["attachment"].ids,
            )
        return res

        # return {"success": True, "xml_document": dte_json, "cdr": "cdr"}
        # return {"error": "Error demo", "blocking_level": "error"}

    def _tgr_l10n_sv_edi_cancel_invoice_step_1(self, invoices):
        self.ensure_one()
        credentials = self._get_dte_credentials(invoices[0])
        dte_model = self.env["l10n_sv.dte.anulacion"]
        message = "La cancelación esta en proceso en el lado del M.H."
        anulacion_json = dte_model.generate_json(invoices[0], credentials)
        anulacion_json_sign = self._tgr_l10n_sv_edi_sign_json(anulacion_json, credentials)
        if anulacion_json_sign.get("error"):
            return {
                invoice: {
                    "error": anulacion_json_sign["error"],
                    "blocking_level": "error",
                }
                for invoice in invoices
            }
        # send anulacion_json
        token = self._get_token(force_request=True, invoice=invoices[0])
        credentials = self._get_dte_credentials(invoices[0])
        if "error" in token:
            return {invoice: {"error": token["error"], "blocking_level": "error"} for invoice in invoices}

        # send to api dte steep 1
        url = "%s/fesv/anulardte" % credentials["api_url"]

        payload = {
            "ambiente": "01" if credentials["environment"] == "prod" else "00",
            "idEnvio": 1,
            "version": anulacion_json["identificacion"]["version"],
            "documento": anulacion_json_sign["body"],
        }
        headers = {
            "User-Agent": "Tagre-dte-sv",
            "Content-Type": "application/JSON",
            "Authorization": token["token"],
        }

        try:
            response = requests.request("POST", url, headers=headers, json=payload, verify=True, timeout=20)
        except requests.exceptions.RequestException as e:
            return {invoice: {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["request"], e))} for invoice in invoices}
        try:
            response_json = response.json()
        except JSONDecodeError as e:
            return {invoice: {"error": str(Markup("%s<br/>%s") % (ERROR_MESSAGES["json_decode"], e))} for invoice in invoices}
        if response_json.get("codigoMsg") not in ["001", "002"] or response.status_code != 200:
            error_msg = str(Markup("%s<br/>: %s") % (ERROR_MESSAGES["response_code"], response_json))
            return {invoice: {"error": error_msg} for invoice in invoices}
        res = {}
        anulacion_json["firmaElectronica"] = anulacion_json_sign["body"]
        anulacion_json["selloRecibido"] = response_json.get("selloRecibido")
        # Chatter.
        json_data = json.dumps(anulacion_json, indent=2, ensure_ascii=False)
        json_data_base64 = base64.b64encode(json_data.encode("utf-8"))

        message = "El documento EDI/DTE fue cancelado con éxito por el M.H."
        res["attachment"] = self.env["ir.attachment"].create(
            {
                "res_model": invoices[0]._name,
                "res_id": invoices[0].id,
                "type": "binary",
                "name": "%s.json" % anulacion_json["identificacion"]["codigoGeneracion"],
                "datas": json_data_base64,
                "mimetype": "application/json",
            }
        )
        for invoice in invoices:
            invoice.write(
                {
                    "tgr_l10n_sv_edi_cancel_sello_recibido": response_json.get("selloRecibido", False),
                    "tgr_l10n_sv_edi_cancel_json_binary": json_data_base64,
                    "tgr_l10n_sv_edi_cancel_json_name": "%s.json" % anulacion_json["identificacion"]["codigoGeneracion"],
                }
            )
            invoice.with_context(no_new_invoice=True).message_post(
                body=message,
                attachment_ids=res["attachment"].ids,
            )

        # return {invoice: {"error": message, "blocking_level": "info"} for invoice in invoices}
        return {invoice: {"success": True} for invoice in invoices}

    # ----------------------------------------------------------------------------
    # Json Electronic Invoice Generate
    # ----------------------------------------------------------------------------

    def _is_compatible_with_journal(self, journal):
        return journal.type == "sale" and journal.company_id.country_code == "SV"

    def _get_move_applicability(self, move):
        self.ensure_one()
        if self.code != "sv_dte_1_0":
            return super()._get_move_applicability(move)
        # print("move_is_dte", move.move_is_dte)
        if move.move_is_dte:
            return {
                "post": self._tgr_l10n_sv_edi_signs_invoice,
                "cancel": self._tgr_l10n_sv_edi_cancel_invoices,
                "cancel_batching": lambda invoice: (invoice.name,),
                "edi_content": self._tgr_l10n_sv_edi_invoice_content,
            }

    def _needs_web_services(self):
        return self.code == "sv_dte_1_0" or super()._needs_web_services()

    def _check_move_configuration(self, move):
        # OVERRIDE
        res = super()._check_move_configuration(move)
        if self.code != "sv_dte_1_0":
            return res
        root_company = move.company_id.l10n_sv_edi_get_root_company()
        partner = move.commercial_partner_id.sudo()
        doc_type = move.l10n_latam_document_type_id.code
        # common values
        if not root_company.partner_id.phone:
            res.append("Falta número de teléfono del emisor")
        if not root_company.vat:
            res.append(f"Falta NIT del emisor: {root_company.display_name}")
        if not root_company.l10n_sv_edi_cod_estable_mh:
            res.append("Falta Código de Establecimiento del emisor MH")
        if not root_company.l10n_sv_edi_cod_estable:
            res.append("Falta Código de Establecimiento del emisor")

        lines = move.invoice_line_ids.filtered(lambda line: line.display_type not in ("line_note", "line_section"))
        for line in lines:
            taxes = line.tax_ids
            if len(taxes) > 1 and len(taxes.filtered(lambda t: t.tax_group_id.l10n_sv_edi_code == "IVA")) > 1:
                res.append('No se pueden tener dos impuestos "IVA" en la misma línea')
        if any(not line.tax_ids for line in move.invoice_line_ids if line.display_type not in ("line_note", "line_section")):
            res.append("Es necesario configurar impuestos en todas las líneas de factura")
        # fe-ccf
        if doc_type == "03":
            if not partner.l10n_sv_nrc:
                res.append("Falta NRC del Cliente")
            if not partner.l10n_sv_edi_economic_activity_id:
                res.append("Falta el código de actividad del cliente")
            if not partner.street or not partner.l10n_sv_district or not partner.city_id or not partner.state_id:
                res.append("Dirección incompleta del cliente")
        if doc_type == "06":
            if not move.debit_origin_id:
                res.append("Falta Documento relacionado.")
            if not move.debit_origin_id.l10n_latam_document_type_id.code in ["07", "03"]:
                res.append("Solo se puede emitir DTE [06] Nota de débito solo a: [03] Comprobante de crédito fiscal")

        # add walidation
        # example
        # res.append('Error etc')
        return res

    def _tgr_l10n_sv_edi_cancel_invoices(self, invoices):
        # OVERRIDE
        if self.code != "sv_dte_1_0":
            return super()._cancel_invoice_edi(invoices)
        company = invoices[0].company_id
        edi_attachments = self.env["ir.attachment"]
        res = {}
        for invoice in invoices:
            if not invoice.tgr_l10n_sv_edi_tipo_invalidacion or not invoice.tgr_l10n_sv_edi_motivo_invalidacion:
                res[invoice] = {"error": "Por favor ponga un motivo de la cancelación"}
                continue
            edi_attachments |= invoice._get_edi_attachment(self)
        # Cancel part 1.
        res.update(self._tgr_l10n_sv_edi_cancel_invoice_step_1(invoices))
        return res

    def _tgr_l10n_sv_edi_invoice_content(self, invoice):
        logging.info("--------------_tgr_l10n_sv_edi_invoice_content --------------")
        return {"name": "hola mundo"}

    def _tgr_l10n_sv_edi_get_tipo_modelo(self, dte_type, invoice):
        tipo_modelo = 1
        if invoice.contingency_event and dte_type in I_T_MODELO_2:
            tipo_modelo = 2
        return tipo_modelo
