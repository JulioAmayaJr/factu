{
    "name": "Pet Grooming Appointments",
    "version": "18.0.1.0.0",
    "summary": "Gestión de citas para veterinaria / grooming",
    "category": "Services",
    "author": "Julio Amaya",
    "license": "LGPL-3",
    "depends": ["base", "mail", "website"],
    "data": [
        "security/ir.model.access.csv",
        "data/grooming_service_data.xml",
        "views/grooming_service_views.xml",
        "views/pet_animal_views.xml",
        "views/medical_history_views.xml",
        "views/grooming_history_views.xml",
        "views/grooming_appointment_views.xml",
        "views/menu_views.xml",
        "views/website_templates.xml",
        "views/website_menu.xml"
    ],
    "installable": True,
    "application": True
}
