# M2 packet 2.5 amendment — runtime casepack registry

Date: 2026-09-15  
Authority: supervisor, following the M2 reconciliation and independent registry contract review  
Base: `6a83b9a` (merged M2.2)

The historical 2.5 spec is useful source material but is not dispatch-ready on its own.
This amendment is binding for the registry builder. It connects registration to the typed
`RuntimePackV1` boundary already consumed by M1 and closes the validator numeric-range gap
(`OS-D1`) before 2.5 is accepted.

## Canonical registry row

The platform-level `casepack` table has no `instance_id`. It stores:

```text
id, pack_key, pack_version, pack_digest, schema_version,
display_name, vertical, rounds, path, validation_json,
registered_at, registered_by
```

`(pack_key, pack_version)` is unique. `pack_digest` is the 64-hex semantic digest produced
by `load_runtime_pack()` for the complete `RuntimePackV1` bundle (casepack plus runtime
supplement). `registered_by` is nullable and may reference `user.id`; auth is not required to
run the registration command. The row is metadata only and has no JSON content columns for
catalogues, preferences, or other pack sections.

## Registration and resolution

`register_casepack(path)` must:

1. constrain the resolved path beneath the configured repository pack root;
2. run the existing 1.2 `validate_pack_dir()` and retain its complete JSON report;
3. refuse every report containing an `ERROR` without inserting a row;
4. load the same directory through `load_runtime_pack()` and persist its semantic digest;
5. verify the metadata identity `(pack_key, pack_version)` from the loaded bundle; and
6. refuse an existing tuple with the message that the version is already registered and must
   be bumped.

Registration is atomic. Warnings are retained and do not block registration. The registry
cache is process-local, keyed by `(pack_key, pack_version)`, and returns an immutable
`RuntimePackV1`. On a cache miss it reloads the path and compares identity and digest with
the row; mismatches raise a registry-integrity error and are never cached. Registered pack
files are append-only operationally; an edited file requires a new version.

`resolve_runtime_pack(session, pack_key, pack_version)` is the adapter for M1's
`SimulationService` boundary. It returns the registered `RuntimePackV1`, so the run's
existing `pack_digest` remains the authoritative persisted execution pin. A registry row
without a valid runtime supplement cannot be resolved for execution.

## Instance binding

`InstanceService.bind_pack(instance_id, pack_key, pack_version)` requires a registered tuple,
copies its `pack_digest` into the instance binding, and refuses rebinding once
`current_round > 0` or the instance has left setup. Existing instances remain pinned when a
new version is registered. Arbitrary unregistered `pack_key`/`pack_version` values may not
create a new instance binding.

The M2 registry fixture is a copied, runtime-capable isolation pack with a distinct tuple;
it is explicitly an isolation fixture, not the substantive second vertical required by
Phase 6. `minimal_valid` remains a validator-only fixture because it has no `runtime.yaml`
and cannot be passed to `load_runtime_pack()`.

## Validator follow-up

`OS-D1` is closed in this packet with field-aware `E19` numeric-range diagnostics. A
range-invalid fixture must name the source file and field and must not emit bare `E00` for
that same violation. The existing fixture matrix and full validator gate remain required;
invoking the validator alone is not evidence of closure.

## Required evidence

- migration upgrade → downgrade → upgrade on SQLite and PostgreSQL;
- schema guard: metadata-only `casepack`, unique tuple, no `instance_id`;
- clean Riverside registration and clean isolation-pack registration;
- broken pack refusal, warning retention, duplicate refusal, path escape refusal;
- cache parse-once proof and digest mismatch refusal;
- binding refusal for unregistered and advanced instances, plus old-version stability;
- registry-to-`RuntimePackV1` resolution and M1 service compatibility;
- `E19` fixture and `OS-D1` no-`E00` proof;
- two-instance/different-pack isolation canary and existing 19-table scope canary;
- full `make check` and `git diff --check`.

The packet does not implement auth, browser UI, scheduling, pack authoring/editing, or a
substantive Phase 6 vertical.
