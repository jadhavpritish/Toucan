clean:
	pipenv --rm

init:
	pipenv install PipFile --dev

format:
	pipenv run python -m isort . --atomic
	pipenv run python -m black .

jupyter-notebook:
	pipenv run jupyter notebook