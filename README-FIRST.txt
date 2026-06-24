Codex Companion

Full README: README.md (English) / README.zh-CN.md (中文)

1. Unzip the package.
2. Double-click: Install Codex Companion.command
   Or from Terminal, Run: ./install.sh
3. Restart MarginNote 4.
4. Open a notebook and click the Codex Companion toolbar icon.
5. If the panel says the MN4 runtime is stale:
   Double-click: Refresh MN Runtime.command
   This asks the open MN4 plugin to reload the Codex panel, re-report native capabilities, and write CodexCompanion-MNRuntimeEvidence-*.json to your Desktop. It does not quit MarginNote 4.
   If evidence says missingNativeHandlerFeatures includes native-highlight-prefer-next-selection-v1, restart MarginNote 4; Web panel reload alone cannot hot-load the native main.js handler.
   You can double-click: Restart MarginNote 4.command
   If that evidence reports ready=True, include it in final acceptance with:
   python3 release_acceptance.py --mn-runtime-evidence ./CodexCompanion-MNRuntimeEvidence-....json
6. To remove the LaunchAgent and MN4 extension:
   Double-click: Uninstall Codex Companion.command
   Run: ./uninstall.sh
7. Optional package check:
   Run: python3 release_smoke_test.py
8. Optional final release gate:
   Run: python3 release_acceptance.py
   This returns non-zero until single-document acceptance, native highlight, signed/notarized pkg, and cross-machine install evidence are complete.
9. Optional release handoff bundle:
   Double-click: Prepare Release Handoff.command
   Or from Terminal, Run: python3 prepare_release_handoff.py
   This writes a handoff folder/zip with latest artifacts, SHA256SUMS, release_acceptance.json, remaining gate next actions, and evidence templates.
   Valid evidence files are placed under evidence/. Stale, incomplete, scope-mismatched, or wrong-package evidence is kept under diagnostics/evidence/ and is not release proof.
10. Optional native highlight evidence:
   In MarginNote 4, open the target PDF. You may select text first, or run the command first and reselect a short PDF span within 90 seconds.
   Double-click: Collect Native Highlight Evidence.command
   This writes codex-companion-native-highlight-evidence-*.json to your Desktop.
   The command first asks the open MN4 plugin to run 高亮下一选区, keeps waiting through the next-selection armed state, then records posted/failed evidence.
   The evidence check matches the latest nativeHighlightSelectionPosted event to ZHIGHLIGHTS rows in the same topic/book scope.
   Or from Terminal, Run:
   python3 release_acceptance.py --collect-native-highlight-evidence ./native-highlight-evidence.json --try-native-highlight
   Then include it in final acceptance with:
   python3 release_acceptance.py --native-highlight-evidence ./native-highlight-evidence.json
11. Optional single-document acceptance:
   While testing with send_action.py, add --record so action results are appended to release/evidence/action-results.jsonl.
   Native highlight evidence is auto-discovered from release/evidence or the Desktop when present; pass --native-highlight-evidence only to force a specific file.
   Then double-click: Collect Single Document Acceptance.command
   Or from Terminal, Run:
   python3 single_document_acceptance.py --topicid <topicid> --bookmd5 <bookmd5> --events events.jsonl --action-results release/evidence/action-results.jsonl --output codex-companion-single-document-acceptance.json
   Then include it in final acceptance with:
   python3 release_acceptance.py --single-document-evidence ./codex-companion-single-document-acceptance.json
12. On a second macOS user or machine, collect install evidence:
   Double-click: Collect Cross-Machine Evidence.command
   This writes codex-companion-cross-machine-evidence-*.json to your Desktop.
   Or from Terminal, Run:
   python3 release_acceptance.py ./CodexCompanion-0.4.22-latest-dist.zip --collect-cross-machine-evidence ./cross-machine-evidence.json
   Then copy cross-machine-evidence.json back and run:
   python3 release_acceptance.py --cross-machine-evidence ./cross-machine-evidence.json
13. Release maintainers can build a macOS pkg wrapper:
   Run: python3 build_pkg.py --dry-run
   Run: python3 build_pkg.py --sign-identity "Developer ID Installer: ..."
   Or double-click: Build Signed Package.command
   This requires exactly one Developer ID Installer certificate in Keychain.
14. Release maintainers can notarize and staple a signed pkg:
   Run: python3 notarize_pkg.py ./CodexCompanion-0.4.22-latest.pkg --keychain-profile "..."
   Or double-click: Notarize Package.command
   This requires a notarytool keychain profile or APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_SPECIFIC_PASSWORD.

The original PDF is not modified. Native "highlight current selection" only runs when MarginNote has an active PDF text selection; annotated PDF export writes a separate copy.
