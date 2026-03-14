from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class TestL10nSvCertificate(TransactionCase):
    def setUp(self):
        super(TestL10nSvCertificate, self).setUp()
        # Crear una compañía de prueba
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        # Generar un par de claves RSA para las pruebas
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.private_key_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self.private_key_b64 = base64.b64encode(self.private_key_bytes).decode()

        self.public_key = self.private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.public_key_b64 = base64.b64encode(self.public_key_bytes).decode()

        # Crear un certificado ficticio en formato XML
        self.certificate_content = f"""
        <CertificadoMH>
            <privateKey>
                <clave>{self.private_key_b64}</clave>
                <encodied>{self.public_key_b64}</encodied>
            </privateKey>
        </CertificadoMH>
        """
        self.certificate_b64 = base64.b64encode(self.certificate_content.encode()).decode()

        # Crear un registro de certificado en Odoo
        self.certificate = self.env["l10n.sv.certificate"].create(
            {
                "content": self.certificate_b64,
                "private_key": self.private_key_b64,
                "company_id": self.company.id,
            }
        )

    def test_certificate_validation(self):
        """Test para validar que el certificado y la clave privada coinciden."""
        self.assertTrue(self.certificate.is_valid, "El certificado debería ser válido.")

    def test_invalid_certificate(self):
        """Test para validar un certificado inválido."""
        # Cambiar la clave privada para que no coincida
        self.certificate.write({"private_key": "clave_privada_invalida"})
        with self.assertRaises(ValidationError):
            self.certificate._check_certificate_and_key()

    def test_signer_dte(self):
        """Test para firmar un DTE usando el certificado."""
        json_dte = '{"invoice": "12345", "amount": 100.0}'
        result = self.certificate.signer_dte(json_dte)
        self.assertEqual(result["status"], "OK", "La firma del DTE debería ser exitosa.")
        self.assertIn("body", result, "El resultado debería contener el token firmado.")

    def test_invalid_signer_dte(self):
        """Test para firmar un DTE con un certificado inválido."""
        self.certificate.write({"private_key": "clave_privada_invalida"})
        json_dte = '{"invoice": "12345", "amount": 100.0}'
        result = self.certificate.signer_dte(json_dte)
        self.assertIn("error", result, "Debería devolver un error al intentar firmar con un certificado inválido.")
