from odoo import fields, models


class GroomingService(models.Model):
    _name = "pet.grooming.service"
    _description = "Servicio Grooming"

    name = fields.Char(string="Nombre", required=True)
    duration_hours = fields.Float(string="Duración (horas)", default=1.0, required=True)
    price = fields.Float(string="Precio")
    active = fields.Boolean(string="Activo", default=True)
