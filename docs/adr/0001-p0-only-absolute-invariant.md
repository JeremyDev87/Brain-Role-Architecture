# ADR 0001: P0 is the only absolute invariant

Status: accepted. P0 contains the minimum truth, safety, provenance, determinism, and no-override core.
P1-P6 remain controlled mutable. A P0 semantic change creates a new architecture identity and major
specification version rather than mutating a running instance.
