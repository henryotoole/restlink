project_name := "restlink"
version := `./.venv/bin/python3 -c "import toml; print(toml.load('./pyproject.toml')['project']['version'])"`

# List only the dependencies that the module actually uses.
listreqs:
	./.venv/bin/pipreqs ./src/{{project_name}} --print --mode no-pin

# Assembles and produces the distributable code in the module release folder.
build:
	python -m build
	cp ./dist/{{project_name}}-{{version}}.tar.gz ./{{project_name}}/{{project_name}}-{{version}}.tar.gz