# Lessons Learned

This file captures helpful lessons from the WiZ addon refactor and testing work.

## Design and refactoring

- Keep behavior at the correct abstraction level.
  - Program logic should own controller behavior, not mutate an external controller just to work around phase shifts.
  - When a feature naturally implies multiple targets, model that explicitly rather than patching a single shared object.

- Favor simpler loops over special-case branches.
  - If a single design can handle both simple and complex cases, use it.
  - In the program dispatch loop, iterating over `controllers` works for both one-controller and many-controller cases.

- Preserve compatibility with existing persistence and UI code.
  - When changing object structure, ensure serialization (`to_dict` / `from_json`) keeps the same external shape.
  - Update user-facing selection and runner logic to operate through program-level IP address accessors.

## Testing

- Add tests for pure logic before adding integration or runtime-dependent tests.
  - This makes refactors safer and avoids needing Kodi to verify core behavior.

- Cover both constructor behavior and runtime semantics.
  - Test how programs are built, how controllers are assigned, and how elapsed-time calculations behave.

- Keep test files small and focused.
  - Separate module-level tests from domain-specific tests.

## Documentation

- Keep versions in sync across `addon.xml`, `README.md`, and `CHANGELOG.md`.
- Use release notes to explain both implementation details and testing improvements.

## Future

- Add CI automation for tests so new changes are validated automatically.
- Consider a small internal design note for the phase-shift controller strategy if more program variants are added.
