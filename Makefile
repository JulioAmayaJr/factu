.PHONY: up down logs shell db-shell build validate reset-clean compose-config

compose-config:
	docker compose config

build:
	docker compose build odoo

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f odoo

shell:
	docker compose exec odoo bash

db-shell:
	docker compose exec db psql -U odoo -d factu_db

validate:
	./scripts/validate_cde.sh

start:
	./scripts/start.sh

reset-clean:
	docker compose down -v
