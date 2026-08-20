"""The scoring engine (module 1.4).

Pure functions: state in, results out. No database, no clock, no randomness, no
I/O (invariant I2). No branch anywhere depends on which casepack is loaded
(invariant I1). The engine emits factor keys, never student-facing prose
(invariant I3); rendering is labels.yaml plus the debrief narrator's job.
"""
