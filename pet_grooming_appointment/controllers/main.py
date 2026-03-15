from datetime import datetime, timedelta

from odoo import http
from odoo.http import request


class PetGroomingWebsiteController(http.Controller):

    @http.route("/pet-grooming", type="http", auth="public", website=True)
    def grooming_form(self, **kwargs):
        services = request.env["pet.grooming.service"].sudo().search([("active", "=", True)])
        return request.render("pet_grooming_appointment.website_pet_grooming_form", {
            "services": services,
            "success": kwargs.get("success"),
            "error": kwargs.get("error"),
        })

    @http.route("/pet-grooming/submit", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def grooming_submit(self, **post):
        try:
            owner_name = (post.get("owner_name") or "").strip()
            phone = (post.get("phone") or "").strip()
            email = (post.get("email") or "").strip()
            pet_name = (post.get("pet_name") or "").strip()
            species = post.get("species") or "dog"
            breed = (post.get("breed") or "").strip()
            color = (post.get("color") or "").strip()
            sex = post.get("sex") or False
            service_id = int(post.get("service_id"))
            date_str = post.get("date")
            hour_str = post.get("hour")
            notes = (post.get("notes") or "").strip()

            if not owner_name or not pet_name or not service_id or not date_str or not hour_str:
                return request.redirect("/pet-grooming?error=1")

            appointment_start = datetime.strptime(f"{date_str} {hour_str}", "%Y-%m-%d %H:%M")

            partner = request.env["res.partner"].sudo().search([
                "|",
                ("email", "=", email),
                ("phone", "=", phone),
            ], limit=1)

            if not partner:
                partner = request.env["res.partner"].sudo().create({
                    "name": owner_name,
                    "phone": phone,
                    "email": email,
                })

            pet = request.env["pet.animal"].sudo().search([
                ("name", "=", pet_name),
                ("partner_id", "=", partner.id),
            ], limit=1)

            if not pet:
                pet = request.env["pet.animal"].sudo().create({
                    "name": pet_name,
                    "partner_id": partner.id,
                    "species": species,
                    "breed": breed,
                    "color": color,
                    "sex": sex,
                })

            request.env["pet.grooming.appointment"].sudo().create({
                "partner_id": partner.id,
                "pet_id": pet.id,
                "service_id": service_id,
                "appointment_start": appointment_start,
                "notes": notes,
                "state": "confirmed",
            })

            return request.redirect("/pet-grooming?success=1")
        except Exception:
            return request.redirect("/pet-grooming?error=1")

    @http.route("/pet-grooming/available_slots", type="json", auth="public", website=True, csrf=False)
    def available_slots(self, date=None, service_id=None):
        if not date or not service_id:
            return []

        service = request.env["pet.grooming.service"].sudo().browse(int(service_id))
        duration = service.duration_hours or 1.0
        base_date = datetime.strptime(date, "%Y-%m-%d")

        appointments = request.env["pet.grooming.appointment"].sudo().search([
            ("state", "!=", "cancelled"),
        ])

        slots = []
        for hour in range(8, 17):
            start_dt = base_date.replace(hour=hour, minute=0, second=0)
            end_dt = start_dt + timedelta(hours=duration)

            occupied = False
            for appt in appointments:
                if appt.appointment_start and appt.appointment_end:
                    if appt.appointment_start < end_dt and appt.appointment_end > start_dt:
                        occupied = True
                        break

            if not occupied:
                slots.append({
                    "value": start_dt.strftime("%H:%M"),
                    "label": start_dt.strftime("%H:%M"),
                })

        return slots
