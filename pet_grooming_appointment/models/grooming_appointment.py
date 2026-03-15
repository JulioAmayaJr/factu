from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GroomingAppointment(models.Model):
    _name = "pet.grooming.appointment"
    _description = "Cita Grooming"
    _order = "appointment_start desc"

    name = fields.Char(string="Referencia", default="Nueva")
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    pet_id = fields.Many2one("pet.animal", string="Mascota", required=True)
    service_id = fields.Many2one("pet.grooming.service", string="Servicio", required=True)

    appointment_start = fields.Datetime(string="Inicio", required=True)
    duration_hours = fields.Float(string="Duración (horas)", related="service_id.duration_hours", store=True)
    appointment_end = fields.Datetime(string="Fin", compute="_compute_end", store=True)

    state = fields.Selection([
        ("draft", "Borrador"),
        ("confirmed", "Confirmada"),
        ("done", "Completada"),
        ("cancelled", "Cancelada"),
    ], string="Estado", default="confirmed")

    notes = fields.Text(string="Notas")

    @api.depends("appointment_start", "duration_hours")
    def _compute_end(self):
        for rec in self:
            if rec.appointment_start and rec.duration_hours:
                rec.appointment_end = rec.appointment_start + timedelta(hours=rec.duration_hours)
            else:
                rec.appointment_end = False

    @api.constrains("appointment_start", "appointment_end", "state")
    def _check_overlap(self):
        for rec in self:
            if not rec.appointment_start or not rec.appointment_end or rec.state == "cancelled":
                continue

            overlap = self.search([
                ("id", "!=", rec.id),
                ("state", "!=", "cancelled"),
                ("appointment_start", "<", rec.appointment_end),
                ("appointment_end", ">", rec.appointment_start),
            ], limit=1)

            if overlap:
                raise ValidationError("Ese horario ya está ocupado.")

    def action_done(self):
        for rec in self:
            rec.state = "done"
            self.env["pet.grooming.history"].create({
                "pet_id": rec.pet_id.id,
                "appointment_id": rec.id,
                "date": rec.appointment_start,
                "service_id": rec.service_id.id,
                "notes": rec.notes or "",
            })
