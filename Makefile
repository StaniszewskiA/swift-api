setup: ## Install development dependencies
	@REM check if poetry is installed
	@poetry --version >nul 2>&1 || (echo Poetry is not installed, please install it && exit 1)

	@REM install dependencies
	poetry sync --with dev
	poetry run pre-commit install

uvicorn-server:  ## Run the uvicorn server
	poetry run uvicorn app.main:app --reload --port 8080

test: ## Run tests
	poetry run ruff check

test-coverage: ## Run tests and calculate test coverage
	@if exist .tmp_coverage_files rmdir /s /q .tmp_coverage_files
	-@mkdir .tmp_coverage_files
	poetry run pytest --cov=app tests -W always
	-@rmdir /s /q .tmp_coverage_files