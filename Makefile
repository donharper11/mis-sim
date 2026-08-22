# mis-sim — verification entry points.
#
# `make check` is the ONE command the pre-merge gate and CI run (QUALITY_PROTOCOL rung 2).
# It runs pytest AND every backend/tests/check_*.py AND the fixture matrix, and exits
# non-zero if any of them does. The check_*.py scripts are picked up by glob, so a NEW
# guard is included automatically -- a guard that runs only when invoked by path does not
# count as shipped (finding 1.5-RC-004; the B5 label routing rotted unguarded for two
# packets, CU-003).

.PHONY: check
check:
	@cd backend && fail=0; \
	echo "== pytest =="; \
	PYTHONPATH=. python3 -m pytest -q || fail=1; \
	for c in tests/check_*.py; do \
	  echo "== $$c =="; \
	  PYTHONPATH=. python3 "$$c" || fail=1; \
	done; \
	if [ $$fail -ne 0 ]; then echo; echo "make check: FAILED"; exit 1; fi; \
	echo; echo "make check: all guards green"
