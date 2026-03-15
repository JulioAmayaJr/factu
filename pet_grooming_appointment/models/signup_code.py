from odoo import fields, models


class PetPortalSignupCode(models.Model):
    _name = "pet.portal.signup.code"
    _description = "Pet Portal Signup Code"
    _order = "create_date desc"

    email = fields.Char(string="Email", required=True, index=True)
    code = fields.Char(string="Code", required=True)
    expires_at = fields.Datetime(string="Expires At", required=True)
    verified = fields.Boolean(string="Verified", default=False)
