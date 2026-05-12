.PHONY: test build publish lint

test:
	pytest tests -v

build:
	python -m build

publish: build
	twine upload dist/*

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/
