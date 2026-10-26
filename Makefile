-include .env
export LICHESS_TOKEN

SYNC := uv run tools/lichess_sync.py
COLOR ?= white
PGN := repertoire/$(COLOR).pgn

.PHONY: sync dry-run prune check-study

sync: check-study
	$(SYNC) --orientation $(COLOR) $(PGN) $(STUDY)

dry-run: check-study
	$(SYNC) --orientation $(COLOR) --dry-run $(PGN) $(STUDY)

prune: check-study
	$(SYNC) --orientation $(COLOR) --prune $(PGN) $(STUDY)

check-study:
	@test -n "$(STUDY)" || { echo "Set STUDY=<study id>, e.g. make sync STUDY=abcd1234"; exit 1; }
