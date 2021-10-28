

build:
	/bin/true

fmt:
	black *.py

lint:
	/bin/true

test:
	/bin/true

check: test

.PHONY: build fmt lint test check
