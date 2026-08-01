# Versioning and migration

The 0.x line is experimental. Backward-compatible additions increment MINOR; corrections increment
PATCH. Breaking schema, precedence, or P0 semantics increment MAJOR. P0 semantic changes also create a
new architecture identity and use an owner-controlled out-of-band migration with explicit rollback.
