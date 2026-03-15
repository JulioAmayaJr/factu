from odoo import fields, models


class PetMedicalHistory(models.Model):
    _name = "pet.medical.history"
    _description = "Historial Clínico"
    _order = "date desc"

    pet_id = fields.Many2one("pet.animal", string="Mascota", required=True, ondelete="cascade")
    date = fields.Date(string="Fecha", required=True, default=fields.Date.context_today)
    diagnosis = fields.Char(string="Diagnóstico")
    treatment = fields.Text(string="Tratamiento")
    observations = fields.Text(string="Observaciones")
    veterinarian = fields.Char(string="Veterinario")
