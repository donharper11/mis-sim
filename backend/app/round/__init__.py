"""Round runner (module 1.6) -- the orchestrator that turns pure engine snapshots into
persisted, immutable round results. Session-touching by design; lives outside app.engine so
the engine stays pure (I2)."""
