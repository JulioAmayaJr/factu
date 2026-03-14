from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xmltodict
import hashlib
import base64
import json
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

SHA256 = "SHA-256"
SHA512 = "SHA-512"
RSA = "RSA"
SHA256WITHRSA = "SHA256withRSA"
SHA1WITHRSA = "SHA1withRSA"
keysize = 2048


class L10nSvCertificate(models.Model):
    _name = "l10n_sv.certificate"
    _description = "Certificado .crt"

    name = fields.Char(string="Nombre")
    content = fields.Binary(string="Certificado", readonly=False, required=True)
    private_key = fields.Char(string="Clave privada")
    encodied_key = fields.Text("encodied", readonly=True)
    is_valid = fields.Boolean(string="Activo", default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", string="Compañia", required=True, default=lambda self: self.env.company, ondelete="cascade"
    )

    @api.constrains("content", "private_key")
    def _check_certificate_and_key(self):
        for rec in self:
            if not rec.content and not rec.private_key:
                continue
            try:
                content = base64.b64decode(self.content)
                certificate = xmltodict.parse(content)["CertificadoMH"]
                crypto = self.encrypt(rec.private_key, SHA512)

                if certificate["privateKey"]["clave"] != crypto:
                    raise ValidationError("La Clave privada no coicide con el certificado ")
                else:
                    self.encodied_key = certificate["privateKey"]["encodied"]
            except Exception as e:
                raise ValidationError("Error al procesar el certificado %s" % str(e))

    def encrypt(self, p, sha=SHA256) -> str:
        h = hashlib.new(sha.lower())
        h.update(p.encode("utf-8"))
        return h.hexdigest()

    @api.model
    def signer_dte(self, json_dte):
        try:
            private_key_dic = self._bytes_to_private_key(str(self.encodied_key).encode())
            if private_key_dic.get("error"):
                return private_key_dic
            jws_token = jwt.encode(json_dte, key=private_key_dic["private_key"], algorithm="RS512")
            res = {"status": "OK", "body": jws_token}
            return res
        except Exception as e:
            return {"error": str(e)}

    def _bytes_to_private_key(self, b64_bytes):
        """Convierte el encodied (Base64 PKCS#8 DER) a clave privada RSA."""
        private_key_der = base64.b64decode(b64_bytes)
        private_key = serialization.load_der_private_key(private_key_der, password=None)
        if not isinstance(private_key, RSAPrivateKey):
            return {"error": "La clave privada no es del tipo RSA"}
        return {"private_key": private_key}
