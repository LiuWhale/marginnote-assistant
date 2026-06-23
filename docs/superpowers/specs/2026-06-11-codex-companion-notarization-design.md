# Codex Companion Notarization Gate Design

## Goal

Make the macOS pkg release path honest enough for public distribution by adding notarization tooling, doctor evidence, and a final acceptance gate that distinguishes unsigned, signed-only, and signed-plus-notarized packages.

## Scope

This iteration does not fake Apple credentials or claim that the local machine can notarize without a Developer ID Installer certificate and App Store Connect credentials. It adds the release machinery and verification gates so a maintainer with credentials can notarize, staple, and prove Gatekeeper readiness.

## Architecture

`build_pkg.py` remains responsible for building and signing the pkg wrapper. A new `notarize_pkg.py` handles `xcrun notarytool submit`, waits for Apple notarization, staples the ticket with `xcrun stapler staple`, and validates the stapled ticket with `xcrun stapler validate`. A double-click `Notarize Package.command` wraps the script for maintainers.

`doctor.py` extends `Latest RC pkg` evidence with both signature and notarization state. `release_acceptance.py` keeps `signed_pkg` as a separate gate and adds `notarized_pkg`, so a signed pkg can be recognized without being accepted as public-ready. The release zip smoke test and packager require the notarization entry points at package root.

## Data Flow

1. Maintainer builds a signed pkg with `build_pkg.py --sign-identity ...` or `Build Signed Package.command`.
2. Maintainer runs `notarize_pkg.py <pkg> --keychain-profile <profile>` or the double-click command.
3. `notarize_pkg.py` submits the pkg with `notarytool --wait`, staples the accepted ticket, validates the staple, and prints JSON when requested.
4. `doctor.py` checks local and OneDrive pkg hashes, `pkgutil --check-signature`, `pkgutil --payload-files`, `xcrun stapler validate`, and `spctl -a -vv -t install`.
5. `release_acceptance.py` blocks final release unless both `signed_pkg` and `notarized_pkg` pass, along with the existing runtime/native/cross-machine gates.

## Error Handling

- Missing pkg: fail with a concise message and no traceback.
- Missing credentials: fail before submission with exact environment/profile options.
- Apple rejection or command failure: preserve return code, stdout, and stderr in JSON evidence.
- Missing Xcode command-line tools: report the missing `xcrun` path as a local environment blocker.
- Notarization unavailable on the current machine must remain a blocker, not a warning, for public release.

## Verification

- Unit tests cover credential resolution, command construction, CLI error handling, doctor notarization evidence, and acceptance gates.
- Static checks compile the new Python script and validate the new shell command.
- Smoke tests require `notarize_pkg.py` and `Notarize Package.command` in release zips.
- Final acceptance must report `notarized_pkg` as blocked on the current machine until a real stapled package exists.

