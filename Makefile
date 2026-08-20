OUT ?= ./index.html

.DEFAULT_GOAL := all
.PHONY: all debug record clean help

## all: build ./index.html from content.md (default)
all: Makefile content.md build.py assets/theme.css assets/app.js assets/tailwind.config.js assets/replay.json
	./build.py --out $(OUT)

## record: re-record the hero terminal replay by running the build for real
record:
	./record.py

## debug: build, serve on http://localhost:4347, open a browser, rebuild on change
debug:
	./build.py --out $(OUT) --watch

## clean: remove generated files
clean:
	rm -f $(OUT)

## help: list targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  make /'
