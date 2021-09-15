serve:
	python3 manage.py runserver

shell:
	python3 manage.py shell_plus

import:
	python3 manage.py run_pipeline_import

scan:
	python3 manage.py run_tns_scan

pulldb:
	-docker start tde-postgres
	-docker exec -e PGPASSWORD='postgres' -it tde-postgres dropdb tdeexchange -Upostgres
	PGPASSWORD='postgres' heroku pg:pull DATABASE_URL "postgresql://postgres@localhost:5432/tdeexchange?sslmode=disable"
