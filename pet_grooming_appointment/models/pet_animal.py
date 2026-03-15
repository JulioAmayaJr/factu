from odoo import api, fields, models


DOG_DEFAULT = "https://i.pinimg.com/736x/d3/3c/06/d33c06ed8d607c70de9dc22b8c9b3830.jpg"
CAT_DEFAULT = "https://png.pngtree.com/png-clipart/20231014/original/pngtree-funny-cat-cartoon-png-image_13300473.png"


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
    age_text = fields.Char(string="Edad")
    color = fields.Char(string="Color")
    sex = fields.Selection([
        ("male", "Macho"),
        ("female", "Hembra"),
    ], string="Sexo")
    weight = fields.Float(string="Peso")
    is_vaccinated = fields.Boolean(string="Vacunado")
    vaccine_notes = fields.Text(string="Vacunas aplicadas")
    sterilized = fields.Boolean(string="Esterilizado")
    allergies = fields.Text(string="Alergias")
    medical_notes = fields.Text(string="Notas médicas")
    notes = fields.Text(string="Notas generales")
    active = fields.Boolean(default=True)

    image_1920 = fields.Image(string="Foto")
    default_image_url = fields.Char(string="Imagen por defecto", compute="_compute_default_image_url")

    appointment_ids = fields.One2many("pet.grooming.appointment", "pet_id", string="Citas")
    medical_history_ids = fields.One2many("pet.medical.history", "pet_id", string="Historial clínico")
    grooming_history_ids = fields.One2many("pet.grooming.history", "pet_id", string="Historial grooming")

    @api.depends("species")
    def _compute_default_image_url(self):
        for rec in self:
            if rec.species == "cat":
                rec.default_image_url = CAT_DEFAULT
            else:
                rec.default_image_url = DOG_DEFAULT
