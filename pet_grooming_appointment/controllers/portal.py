from datetime import datetime
import base64
import pytz

from odoo import http
from odoo.http import request


class PetGroomingPortalController(http.Controller):

    @http.route('/my/pets', type='http', auth='user', website=True)
    def my_pets(self, **kwargs):
        partner = request.env.user.partner_id
        pets = request.env['pet.animal'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='name asc')

        return request.render('pet_grooming_appointment.portal_my_pets', {
            'pets': pets,
            'page_name': 'my_pets',
        })

    @http.route('/my/pets/new', type='http', auth='user', website=True)
    def my_pets_new(self, **kwargs):
        return request.render('pet_grooming_appointment.portal_pet_form', {
            'page_name': 'my_pets_new',
            'error': kwargs.get('error'),
            'pet': False,
            'form_action': '/my/pets/create',
        })

    @http.route('/my/pets/create', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def my_pets_create(self, **post):
        try:
            partner = request.env.user.partner_id
            name = (post.get('name') or '').strip()
            species = post.get('species') or 'dog'
            breed = (post.get('breed') or '').strip()
            color = (post.get('color') or '').strip()
            sex = post.get('sex') or False
            birthdate = post.get('birthdate') or False
            age_text = (post.get('age_text') or '').strip()
            weight = float(post.get('weight') or 0)
            is_vaccinated = bool(post.get('is_vaccinated'))
            vaccine_notes = (post.get('vaccine_notes') or '').strip()
            sterilized = bool(post.get('sterilized'))
            allergies = (post.get('allergies') or '').strip()
            medical_notes = (post.get('medical_notes') or '').strip()
            notes = (post.get('notes') or '').strip()

            if not name:
                return request.redirect('/my/pets/new?error=1')

            existing = request.env['pet.animal'].sudo().search([
                ('partner_id', '=', partner.id),
                ('name', '=ilike', name),
            ], limit=1)

            if existing:
                return request.redirect('/my/pets')

            image_data = False
            uploaded = request.httprequest.files.get('image')
            if uploaded and uploaded.filename:
                image_data = base64.b64encode(uploaded.read())

            request.env['pet.animal'].sudo().create({
                'partner_id': partner.id,
                'name': name,
                'species': species,
                'breed': breed,
                'color': color,
                'sex': sex or False,
                'birthdate': birthdate or False,
                'age_text': age_text,
                'weight': weight,
                'is_vaccinated': is_vaccinated,
                'vaccine_notes': vaccine_notes,
                'sterilized': sterilized,
                'allergies': allergies,
                'medical_notes': medical_notes,
                'notes': notes,
                'image_1920': image_data,
            })

            return request.redirect('/my/pets')
        except Exception:
            return request.redirect('/my/pets/new?error=1')

    @http.route('/my/pets/<int:pet_id>', type='http', auth='user', website=True)
    def my_pet_detail(self, pet_id, **kwargs):
        partner = request.env.user.partner_id
        pet = request.env['pet.animal'].sudo().search([
            ('id', '=', pet_id),
            ('partner_id', '=', partner.id),
        ], limit=1)

        if not pet:
            return request.not_found()

        appointments = request.env['pet.grooming.appointment'].sudo().search([
            ('pet_id', '=', pet.id)
        ], order='appointment_start desc')
        
        medical_history = request.env['pet.medical.history'].sudo().search([
            ('pet_id', '=', pet.id)
        ], order='date desc')
        
        return request.render('pet_grooming_appointment.portal_pet_detail', {
            'pet': pet,
            'appointments': appointments,
            'medical_history': medical_history,
            'page_name': 'my_pet_detail',
        })

    @http.route('/my/pets/<int:pet_id>/edit', type='http', auth='user', website=True)
    def my_pet_edit(self, pet_id, **kwargs):
        partner = request.env.user.partner_id
        pet = request.env['pet.animal'].sudo().search([
            ('id', '=', pet_id),
            ('partner_id', '=', partner.id),
        ], limit=1)

        if not pet:
            return request.not_found()

        return request.render('pet_grooming_appointment.portal_pet_form', {
            'page_name': 'my_pet_edit',
            'error': kwargs.get('error'),
            'pet': pet,
            'form_action': f'/my/pets/{pet.id}/update',
        })

    @http.route('/my/pets/<int:pet_id>/update', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def my_pet_update(self, pet_id, **post):
        try:
            partner = request.env.user.partner_id
            pet = request.env['pet.animal'].sudo().search([
                ('id', '=', pet_id),
                ('partner_id', '=', partner.id),
            ], limit=1)

            if not pet:
                return request.not_found()

            vals = {
                'name': (post.get('name') or '').strip(),
                'species': post.get('species') or 'dog',
                'breed': (post.get('breed') or '').strip(),
                'color': (post.get('color') or '').strip(),
                'sex': post.get('sex') or False,
                'birthdate': post.get('birthdate') or False,
                'age_text': (post.get('age_text') or '').strip(),
                'weight': float(post.get('weight') or 0),
                'is_vaccinated': bool(post.get('is_vaccinated')),
                'vaccine_notes': (post.get('vaccine_notes') or '').strip(),
                'sterilized': bool(post.get('sterilized')),
                'allergies': (post.get('allergies') or '').strip(),
                'medical_notes': (post.get('medical_notes') or '').strip(),
                'notes': (post.get('notes') or '').strip(),
            }

            uploaded = request.httprequest.files.get('image')
            if uploaded and uploaded.filename:
                vals['image_1920'] = base64.b64encode(uploaded.read())

            pet.sudo().write(vals)
            return request.redirect(f'/my/pets/{pet.id}')
        except Exception:
            return request.redirect(f'/my/pets/{pet_id}/edit?error=1')

    @http.route('/my/pet-grooming/book', type='http', auth='user', website=True)
    def my_pet_grooming_book(self, **kwargs):
        partner = request.env.user.partner_id
        pets = request.env['pet.animal'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='name asc')
        services = request.env['pet.grooming.service'].sudo().search([
            ('active', '=', True)
        ], order='name asc')

        return request.render('pet_grooming_appointment.portal_book_appointment', {
            'pets': pets,
            'services': services,
            'success': kwargs.get('success'),
            'error': kwargs.get('error'),
            'page_name': 'my_pet_grooming_book',
        })

    @http.route('/my/pet-grooming/book/submit', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def my_pet_grooming_book_submit(self, **post):
        try:
            partner = request.env.user.partner_id
            pet_id = int(post.get('pet_id'))
            service_id = int(post.get('service_id'))
            date_str = post.get('date')
            hour_str = post.get('hour')
            notes = (post.get('notes') or '').strip()

            pet = request.env['pet.animal'].sudo().search([
                ('id', '=', pet_id),
                ('partner_id', '=', partner.id),
            ], limit=1)

            if not pet or not service_id or not date_str or not hour_str:
                return request.redirect('/my/pet-grooming/book?error=1')

            sv_tz = pytz.timezone("America/El_Salvador")
            local_dt = sv_tz.localize(datetime.strptime(f"{date_str} {hour_str}", "%Y-%m-%d %H:%M"))
            appointment_start = local_dt.astimezone(pytz.UTC).replace(tzinfo=None)

            request.env['pet.grooming.appointment'].sudo().create({
                'partner_id': partner.id,
                'pet_id': pet.id,
                'service_id': service_id,
                'appointment_start': appointment_start,
                'notes': notes,
                'state': 'confirmed',
            })

            return request.redirect('/my/pet-grooming/book?success=1')
        except Exception:
            return request.redirect('/my/pet-grooming/book?error=1')

    @http.route('/my/appointments', type='http', auth='user', website=True)
    def my_appointments(self, **kwargs):
        partner = request.env.user.partner_id
        appointments = request.env['pet.grooming.appointment'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='appointment_start desc')

        return request.render('pet_grooming_appointment.portal_my_appointments', {
            'appointments': appointments,
            'page_name': 'my_appointments',
        })
