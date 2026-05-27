PYTHON  := .venv/bin/python
PYI     := .venv/bin/pyinstaller
SRC     := src
DIST    := dist

# ── Exclusões para o build slim (sem ML) ──────────────────────────────────────
SLIM_EXCLUDES := \
	--exclude-module torch \
	--exclude-module torchvision \
	--exclude-module torchaudio \
	--exclude-module transformers \
	--exclude-module sentence_transformers \
	--exclude-module faiss

# ── Hidden imports que o PyInstaller não detecta automaticamente ───────────────
CLI_HIDDEN := \
	--hidden-import markdown_it

MCP_HIDDEN := \
	--collect-all mcp \
	--hidden-import faiss \
	--hidden-import sentence_transformers \
	--hidden-import sentence_transformers.models \
	--hidden-import sentence_transformers.losses

# ── Flags comuns ───────────────────────────────────────────────────────────────
PYI_FLAGS := --onefile --noupx --paths $(SRC)

.PHONY: all build build-slim build-full build-mcp clean install-build help

all: help

## build-slim   dist/rodoc sem ML (~50 MB) — extract + normalize
build-slim: _check-pyinstaller
	PYTHONPATH=$(SRC) $(PYI) $(PYI_FLAGS) \
		--name rodoc \
		$(CLI_HIDDEN) \
		$(SLIM_EXCLUDES) \
		$(SRC)/main.py
	@echo ""
	@echo "  Binary ready: $(DIST)/rodoc  (extract + normalize only)"

## build-full   dist/rodoc com ML (~2.5 GB) — extract + normalize + index
build-full: _check-pyinstaller
	PYTHONPATH=$(SRC) $(PYI) $(PYI_FLAGS) \
		--name rodoc \
		$(CLI_HIDDEN) \
		$(SRC)/main.py
	@echo ""
	@echo "  Binary ready: $(DIST)/rodoc  (all commands)"

# ─────────────────────────────────────────────────────────────────────────────
## build-mcp    dist/mcp-docs-server com ML (~2.5 GB)
# ─────────────────────────────────────────────────────────────────────────────
build-mcp: _check-pyinstaller
	PYTHONPATH=$(SRC) $(PYI) $(PYI_FLAGS) \
		--name mcp-docs-server \
		$(MCP_HIDDEN) \
		$(SRC)/mcp_docs_server/__main__.py
	@echo ""
	@echo "  Binary ready: $(DIST)/mcp-docs-server"

## build        build-slim + build-mcp  (recomendado)
build: build-slim build-mcp

## install-build  Instala o PyInstaller no venv
install-build:
	$(PYTHON) -m pip install pyinstaller

## clean        Remove artefatos de build (build/, dist/, *.spec)
clean:
	rm -rf build dist *.spec
	@echo "  Cleaned."

## help         Lista os targets disponíveis
help:
	@echo ""
	@echo "Targets:"
	@grep -E '^## ' Makefile | sed 's/^## /  make /'
	@echo ""
	@echo "Exemplos:"
	@echo "  make install-build   # instala PyInstaller"
	@echo "  make build-slim      # rodoc leve (~50 MB), sem ML"
	@echo "  make build-full      # rodoc completo (~2.5 GB), com ML"
	@echo "  make build-mcp       # servidor MCP (~2.5 GB)"
	@echo "  make build           # build-slim + build-mcp"
	@echo ""

# ── Interno ───────────────────────────────────────────────────────────────────
_check-pyinstaller:
	@test -f $(PYI) || { \
		echo ""; \
		echo "  PyInstaller não encontrado. Execute: make install-build"; \
		echo ""; \
		exit 1; \
	}
