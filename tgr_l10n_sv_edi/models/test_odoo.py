from odoo import fields, models


class OdooTest(models.Model):
    _name = "odoo.test"

    name = fields.Char("aoeu")
