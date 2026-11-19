# Kasa 0.4.0-alpha — Release notes draft (not published)

**Release status:** Engineering draft only. **No official signed or notarized public release** has been approved. License decision remains pending.

## Demonstrated during local development

- C++20 independent native compiler/VM; KBC1 on-disk bytecode with checksum and verifier.
- Python behavioral reference and JavaScript browser runtime; structured beginner-oriented diagnostics.
- Intel macOS Ventura 13.7.8 real-machine user logs: 19/19 local full verification stages passed; local unsigned installer 0.4.0.194 installed and subsequently upgraded to 0.4.0.202. Kasa programs ran via the system-installed executable without active Python venv.
- SHA-256 checksum verification of local macOS installer.
- Academy full first-party Kasa Studio using WASM plus JavaScript fallback, and standalone Netlify playground separately.

## Known limitations

- Language syntax, built-ins, standard library and modules remain limited relative to established languages.
- Native alpha integers have narrower bounds than Python reference unless experimental bigint build enabled.
- Real Apple Silicon, new Windows and Linux installer release checks remain outstanding.
- KBC1 remains experimental; untrusted bytecode is not security-certified.
- Mac system uninstaller and interrupted-upgrade recovery remain pre-release.
- Native-speaker/educator review and classroom assessments pending.
- Signing/notarization, formal software license, outside testers, support policy and maintenance cadence pending.
- Browser release manifest passing tests does not prove production deployment has updated; verify live site separately.

## Next release gates

See `docs/RELEASE_CHECKLIST.md`, `docs/LANGUAGE_COMPATIBILITY_POLICY.md`, `scripts/audit_public_alpha.py` and `docs/PHASE_5B_INSTALLERS_AND_UPGRADES.md`.

Do not publish download links or describe this draft as a stable or fully supported release. Release notes must be reviewed and approved before publication.
