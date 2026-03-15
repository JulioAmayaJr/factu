from odoo import fields, models


class PetGroomingHistory(models.Model):
    _name = "pet.grooming.history"
    _description = "Historial de Grooming"
    _order = "date desc"

    pet_id = fields.Many2one("pet.animal", string="Mascota", required=True, ondelete="cascade")
    appointment_id = fields.Many2one("pet.grooming.appointment", string="Cita")
    date = fields.Datetime(string="Fecha", required=True, default=fields.Datetime.now)
    service_id = fields.Many2one("pet.grooming.service", string="Servicio")
    notes = fields.Text(string="Notas")
    hairstyle = fields.Char(string="Tipo de corte")
    bath_done = fields.Boolean(string="Baño realizado")
    haircut_done = fields.Boolean(string="Corte realizado")
    nails_done = fields.Boolean(string="Uñas realizadas")
