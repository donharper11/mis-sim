"""The 1.7 calibration harness -- the measuring instrument for the Phase-1 calibration gate.

It seeds four scripted team archetypes, runs each through the REAL round-runner for six rounds,
and prints the score curves a human reviews. It is MECHANICAL and DETERMINISTIC: it runs, produces
the curves + term decomposition + diagnostics + the live TODO:calibrate inventory, and hands them
to the calibration authority. **It does not rule.** It never exits non-zero on a dominance
condition and never asserts G1-G4 as pass/fail (spec decision 5 / O3 / I6). The judgment -- is
there a dominant strategy? -- is the authority's (spec section 5.4).
"""
