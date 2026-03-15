from datetime import timedelta
import random
import smtplib
import traceback

from email.message import EmailMessage

from odoo import http, fields
from odoo.http import request


class PetPortalRegisterController(http.Controller):

    def _send_code_email(self, to_email, code):
        icp = request.env["ir.config_parameter"].sudo()

        smtp_host = icp.get_param("pet_signup.smtp_host")
        smtp_port = int(icp.get_param("pet_signup.smtp_port", "587"))
        smtp_user = icp.get_param("pet_signup.smtp_user")
        smtp_pass = icp.get_param("pet_signup.smtp_pass")
        smtp_from = icp.get_param("pet_signup.smtp_from")

        print("SMTP CONFIG DEBUG:", {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_from": smtp_from,
            "smtp_pass_set": bool(smtp_pass),
        })

        if not smtp_host or not smtp_port or not smtp_user or not smtp_pass or not smtp_from:
            raise Exception("SMTP no configurado correctamente.")

        msg = EmailMessage()
        msg["Subject"] = "Código de verificación - Pet Grooming"
        msg["From"] = smtp_from
        msg["To"] = to_email
        msg.set_content(
            f"Tu código de verificación es: {code}\n\n"
            f"Este código vence en 10 minutos."
        )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

    @http.route("/register", type="http", auth="public", website=True)
    def register_form(self, **kwargs):
        return request.render("pet_grooming_appointment.website_register_form", {
            "error": kwargs.get("error"),
        })

    @http.route("/register/send-code", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def register_send_code(self, **post):
        try:
            name = (post.get("name") or "").strip()
            email = (post.get("email") or "").strip().lower()
            password = post.get("password") or ""
            confirm_password = post.get("confirm_password") or ""

            if not name or not email or not password or not confirm_password:
                return request.redirect("/register?error=missing")

            if password != confirm_password:
                return request.redirect("/register?error=password")

            existing_user = request.env["res.users"].sudo().search([
                ("login", "=", email)
            ], limit=1)
            if existing_user:
                return request.redirect("/register?error=exists")

            code = str(random.randint(100000, 999999))
            expires_at = fields.Datetime.now() + timedelta(minutes=10)

            old_codes = request.env["pet.portal.signup.code"].sudo().search([
                ("email", "=", email),
                ("verified", "=", False),
            ])
            old_codes.unlink()

            request.env["pet.portal.signup.code"].sudo().create({
                "email": email,
                "code": code,
                "expires_at": expires_at,
                "verified": False,
            })

            request.session["pet_signup_pending"] = {
                "name": name,
                "email": email,
                "password": password,
            }

            self._send_code_email(email, code)

            return request.redirect("/register/verify")
        except Exception as e:
            print("REGISTER SEND CODE ERROR:", repr(e))
            print(traceback.format_exc())
            return request.redirect("/register?error=send")

    @http.route("/register/verify", type="http", auth="public", website=True)
    def register_verify_form(self, **kwargs):
        pending = request.session.get("pet_signup_pending")
        if not pending:
            return request.redirect("/register")

        return request.render("pet_grooming_appointment.website_register_verify_form", {
            "email": pending.get("email"),
            "error": kwargs.get("error"),
        })

    @http.route("/register/verify/submit", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def register_verify_submit(self, **post):
        try:
            pending = request.session.get("pet_signup_pending")
            if not pending:
                return request.redirect("/register")

            email = pending.get("email")
            name = pending.get("name")
            password = pending.get("password")
            code = (post.get("code") or "").strip()

            rec = request.env["pet.portal.signup.code"].sudo().search([
                ("email", "=", email),
                ("code", "=", code),
                ("verified", "=", False),
            ], limit=1)

            if not rec:
                return request.redirect("/register/verify?error=invalid")

            if rec.expires_at < fields.Datetime.now():
                return request.redirect("/register/verify?error=expired")

            partner = request.env["res.partner"].sudo().create({
                "name": name,
                "email": email,
            })

            portal_group = request.env.ref("base.group_portal")

            request.env["res.users"].sudo().create({
                "name": name,
                "login": email,
                "email": email,
                "partner_id": partner.id,
                "password": password,
                "groups_id": [(6, 0, [portal_group.id])],
            })

            rec.verified = True
            request.session.pop("pet_signup_pending", None)

            return request.redirect("/web/login?login=%s" % email)
        except Exception as e:
            print("REGISTER VERIFY ERROR:", repr(e))
            print(traceback.format_exc())
            return request.redirect("/register/verify?error=server")
