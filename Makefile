PYTHON ?= python3
OUT    := ./index.html
SRC    := content.md build.py assets/theme.css assets/app.js assets/tailwind.config.js

.DEFAULT_GOAL := all
.PHONY: all debug clean help

## all: build ./index.html from content.md (default)
all: $(OUT)
	./check.py $(OUT)

$(OUT): $(SRC)
	./build.py --out $(OUT)

## debug: build, serve on http://localhost:4347, open a browser, rebuild on change
debug:
	./build.py --out $(OUT) --watch

## clean: remove generated files
clean:
	rm -f $(OUT)

## help: list targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  make /'
