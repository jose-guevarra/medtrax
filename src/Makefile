.PHONY: clean


dist:
	#mkdir -p dist/
	#cp -a agent/* dist
	uv pip compile ../pyproject.toml -o agent/requirements.txt
	#uv pip compile ../pyproject.toml -o dist/requirements.txt
	#pip3.14 install --target dist/ -r dist/requirements.txt

clean:
	rm -rf agent/requirements.txt