# Casepack registry operations

Casepacks are registered from directories beneath the configured `CASEPACK_ROOT`
(by default `backend/packs`). Registration runs the full validator and then loads
the runtime supplement through `load_runtime_pack()`. Any `ERROR` refuses the
operation; warnings are retained in the registry report.

The registry key is `(pack_key, pack_version)`. A version is immutable: bump the
version before registering changed content. The registry stores identity, digest,
metadata, path, and the complete validator report. It does not store pack content.

Runtime resolution verifies the on-disk semantic digest against the registered row.
Resolved packs are cached per process by tuple and returned as the immutable
`RuntimePackV1` boundary. A missing runtime supplement, identity mismatch, or digest
mismatch is an integrity failure and is never cached.

Instances bind only to registered tuples while still in setup. Binding copies the
semantic `pack_digest` into `simulation_instance`; once round 1 starts, rebinding is
refused. Existing instances therefore remain pinned when a newer version is added.

Registered pack directories are append-only operationally. Editing files in place
without a version bump can make a future process fail digest verification; repair by
restoring the registered files or registering a new version.
