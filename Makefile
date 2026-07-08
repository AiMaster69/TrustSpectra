.PHONY: help install test lint format clean run

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	pip install -r requirements.txt
	pre-commit install

run: ## Запустить приложение
	python run.py

test: ## Запустить тесты
	pytest

test-cov: ## Запустить тесты с покрытием
	pytest --cov=core --cov=ui --cov=utils --cov-report=html

lint: ## Проверить код линтером
	flake8 core ui utils
	mypy core ui utils

format: ## Отформатировать код
	black core ui utils
	isort core ui utils

format-check: ## Проверить форматирование кода
	black --check core ui utils
	isort --check-only core ui utils

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

check: format-check lint test ## Проверить все (форматирование, линтинг, тесты)

setup: install-dev ## Настройка окружения для разработки
	@echo "Окружение для разработки настроено"

ci: format-check lint test-cov ## Команды для CI/CD
