build:
	poetry build

install:
	poetry install

lint:
	poetry run flake8 page_loader

check:
	poetry run pytest tests

test-coverage:
	poetry run pytest --cov=page_loader tests --cov-report xml

package-install:
	pip install --user dist/*.whl
