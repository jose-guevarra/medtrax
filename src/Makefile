.PHONY: clean


dist:
	#mkdir -p dist/
	#cp -a agent/* dist
	uv pip compile mtx_agent/pyproject.toml -o mtx_agent/requirements.txt
	#uv pip compile ../pyproject.toml -o dist/requirements.txt
	#pip3.14 install --target dist/ -r dist/requirements.txt

clean:
	rm -rf mtx_agent/requirements.txt