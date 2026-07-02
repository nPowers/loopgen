.PHONY: check

check:
	python3 tools/verify_loopgen_contracts.py && python3 tools/classify.py --self-test
