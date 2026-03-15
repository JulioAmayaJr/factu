from odoo import fields, models


class PetAnimal(models.Model):
    _name = "pet.animal"
    _description = "Mascota"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    partner_id = fields.Many2one("res.partner", string="Propietario", required=True)
    species = fields.Selection([
        ("dog", "Perro"),
        ("cat", "Gato"),
        ("other", "Otro"),
    ], string="Especie", default="dog", required=True)
    breed = fields.Char(string="Raza")
    birthdate = fields.Date(string="Fecha de nacimiento")
    color = fields.Char(string="Color")
    sex = fields.Selection([
        ("male", "Macho"),
        ("female", "Hembra"),
    ], string="Sexo")
    weight = fields.Float(string="Peso")
    notes = fields.Text(string="Notas generales")

    appointment_ids = fields.One2many("pet.grooming.appointment", "pet_id", string="Citas")
    medical_history_ids = fields.One2many("pet.medical.history", "pet_id", string="Historial clínico")
    grooming_history_ids = fields.One2many("pet.grooming.history", "pet_id", string="Historial grooming")
