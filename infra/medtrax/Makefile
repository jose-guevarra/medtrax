.PHONY: clean



dist:
	mkdir -p dist/
	cp -a ../../src/agent/* dist
	uv pip compile pyproject.toml -o dist/requirements.txt
	pip3.14 install --target dist/ -r dist/requirements.txt

synth: dist
	uv run npx cdk synth

deploy: dist
	uv run npx cdk deploy


clean:
	rm -rf dist/