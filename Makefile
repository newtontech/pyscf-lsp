.PHONY: install format lint typecheck test traceability check cleanup-merged

install:
	bash scripts/install.sh

format:
	bash scripts/format.sh

lint:
	bash scripts/lint.sh

typecheck:
	bash scripts/typecheck.sh

test:
	bash scripts/test.sh

traceability:
	python3 scripts/check_docstring_traceability.py --write-report

check: lint typecheck test traceability

cleanup-merged:
	bash scripts/cleanup_merged_worktrees.sh
