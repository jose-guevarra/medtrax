.PHONY: clean tests



dist:
	mkdir -p dist/
	cp -a ../../src/agent/* dist
	uv pip compile pyproject.toml -o dist/requirements.txt
	pip3.14 install --target dist/ -r dist/requirements.txt


tests:
	uv run pytest tests/unit/test_*.py

synth: dist
	uv run npx cdk synth

deploy: dist
	uv run npx cdk deploy --all


clean:
	rm -rf dist/