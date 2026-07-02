from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ui_functional_acceptance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("codex_mn_ui_functional_acceptance", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UiFunctionalAcceptanceTests(unittest.TestCase):
    def test_static_shell_defaults_to_chat_first_product_mode(self) -> None:
        index_source = (ROOT / "extension/codex.mn.assistant/web/index.html").read_text(encoding="utf-8")
        app_source = (ROOT / "extension/codex.mn.assistant/web/app.js").read_text(encoding="utf-8")

        self.assertIn('data-product-mode="chat"', index_source)
        self.assertNotIn('data-product-mode="workspace"', index_source.split(">", 1)[0])
        self.assertIn("activeProductMode: 'chat'", app_source)

    def test_acceptance_checks_static_ui_and_arbitrary_document_workspace(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            report = module.evaluate_ui_functional_acceptance(
                root=ROOT,
                workspace_home=Path(tmp),
                document_payload={
                    "topicid": "UI-FUNC-TOPIC",
                    "bookmd5": "ui-func-book",
                    "docmd5": "ui-func-book",
                    "documentTitle": "任意文档 UI 功能验收.pdf",
                    "mnObject": {
                        "objectId": "mnobj:doc:ui-functional",
                        "kind": "document",
                        "title": "任意文档 UI 功能验收.pdf",
                        "sourceRef": {"documentTitle": "任意文档 UI 功能验收.pdf"},
                    },
                },
            )

        self.assertEqual(report["schema"], "codex-companion-ui-functional-acceptance-v1")
        self.assertTrue(report["ok"], report)
        checks = {item["id"]: item for item in report["checks"]}
        for check_id in [
            "webview_static_controls",
            "webview_behavior_markers",
            "webview_button_coverage",
            "arbitrary_document_workspace",
            "notebook_workspace_kernels",
            "workspace_surface_actions",
            "native_scope_guards",
        ]:
            self.assertEqual(checks[check_id]["status"], "PASS", checks[check_id])
        self.assertGreaterEqual(checks["webview_static_controls"]["evidence"]["controlCount"], 90)
        self.assertEqual(checks["webview_button_coverage"]["evidence"]["unclassifiedButtons"], [])
        self.assertIn("sendButton", checks["webview_button_coverage"]["evidence"]["actualBrowserButtons"])
        self.assertIn("workspaceNavMindmapStudioButton", checks["webview_button_coverage"]["evidence"]["interactionButtons"])
        self.assertIn("mindmapStudioApplySelectedButton", checks["webview_button_coverage"]["evidence"]["writeButtons"])
        self.assertEqual(checks["notebook_workspace_kernels"]["evidence"]["runbookStepCount"], 8)
        self.assertEqual(checks["notebook_workspace_kernels"]["evidence"]["matrixAxisCount"], 7)
        self.assertEqual(checks["notebook_workspace_kernels"]["evidence"]["intakeRouteCount"], 7)
        self.assertEqual(checks["notebook_workspace_kernels"]["evidence"]["taskDraftCount"], 7)
        self.assertFalse(checks["native_scope_guards"]["evidence"]["noScopeAutoPlanCanRun"])

    def test_cli_writes_json_report(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "ui-functional.json"
            exit_code = module.main(
                [
                    "--root",
                    str(ROOT),
                    "--workspace-home",
                    str(Path(tmp) / "home"),
                    "--topicid",
                    "UI-CLI-TOPIC",
                    "--bookmd5",
                    "ui-cli-book",
                    "--document-title",
                    "任意文档 CLI UI 验收.pdf",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertIn("codex-companion-ui-functional-acceptance-v1", output.read_text(encoding="utf-8"))

    def test_browser_devtools_wait_uses_configured_timeout(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("wait_for_devtools_page_ws(debug_port, timeout_seconds=timeout_seconds)"),
            3,
        )

    def test_browser_render_output_requires_rendered_workspace_controls(self) -> None:
        module = load_module()

        passing = module.check_browser_render_output(
            """
            <main id="aiChatShell" data-product-mode="chat">
              <section id="knowledgeOsContractPanel"></section>
              <section id="workspaceNavigator"></section>
              <section id="notebookWorkspacePanel"></section>
              <section id="notebookKnowledgeMatrix"></section>
              <section id="notebookObjectIntake"></section>
              <section id="notebookObjectTaskComposer"></section>
              <section id="notebookWorkspaceRunbook"></section>
              <section id="workflowBuilderBoardPanel"></section>
              <section id="realMnAcceptancePanel"></section>
              <button id="objectRegistryScanButton" disabled title="缺少 topicid"></button>
              <button id="mindmapTreeRefreshButton" disabled title="缺少 topicid"></button>
              <button id="sendButton"><span>发送</span></button>
            </main>
            """,
            timed_out=False,
            return_code=0,
        )
        self.assertEqual(passing["status"], "PASS", passing)

        failing = module.check_browser_render_output(
            "<main id=\"aiChatShell\"></main>",
            timed_out=False,
            return_code=0,
        )
        self.assertEqual(failing["status"], "FAIL")
        self.assertIn("missing rendered marker", "\n".join(failing["problems"]))

    def test_browser_interaction_result_requires_real_mode_and_surface_switches(self) -> None:
        module = load_module()

        def surface_entry(button_id: str) -> dict:
            expected_surface, expected_pane = module.BROWSER_INTERACTION_EXPECTED_SURFACES[button_id]
            layout_spec = module.BROWSER_INTERACTION_EXPECTED_LAYOUT[button_id]
            visible = {
                element_id: False
                for spec in module.BROWSER_INTERACTION_EXPECTED_LAYOUT.values()
                for element_id in spec["visible"] + spec["hidden"]
            }
            for element_id in layout_spec["visible"]:
                visible[element_id] = True
            for element_id in layout_spec["hidden"]:
                visible[element_id] = False
            return {
                "activeSurface": expected_surface,
                "activePane": expected_pane,
                "layout": {
                    "shellSurface": expected_surface,
                    "visible": visible,
                },
            }

        browser_result = {
                "initialMode": "chat",
                "afterChat": {
                    "mode": "chat",
                    "chatSelected": True,
                    "workspaceNavigatorVisible": False,
                    "layout": {
                        "commandPaneVisible": True,
                        "bodyVisible": True,
                        "historyVisible": True,
                        "composerVisible": True,
                        "historyHeight": 280,
                        "bodyHeight": 340,
                        "composerBottomGap": 8,
                        "historyFillsBody": True,
                        "composerNearViewportBottom": True,
                    },
                },
                "afterWorkspace": {
                    "mode": "workspace",
                    "workspaceSelected": True,
                    "workspaceNavigatorVisible": False,
                    "advancedToolCenterVisible": True,
                    "expertModeExpanded": "false",
                },
                "afterExpertMode": {
                    "expertModeExpanded": "true",
                    "workspaceNavigatorVisible": True,
                    "expertBackVisible": True,
                    "advancedToolCenterVisible": False,
                },
                "consoleLayout": {
                    "knowledgeConsoleVisible": True,
                    "panelHeight": 420,
                    "blankGapAboveCommand": 0,
                    "trailingBlankAboveCommand": 16,
                    "fillsAboveCommand": True,
                    "detailsNestedScrollTrap": False,
                    "detailsOverflowY": "visible",
                    "detailsScrollHeight": 520,
                    "detailsClientHeight": 520,
                },
                "mindmapStudio": {"activeSurface": "mindmap_studio", "activePane": "operation"},
                "cardFactory": {"activeSurface": "card_factory", "activePane": "knowledge"},
                "workflowBuilder": {"activeSurface": "workflow_builder", "activePane": "workflow"},
                "workspaceSurfaces": {
                    button_id: surface_entry(button_id)
                    for button_id in module.BROWSER_INTERACTION_EXPECTED_SURFACES
                },
                "workspaceSelectSurfaces": {
                    "object_browser": {
                        "activeSurface": "object_browser",
                        "activePane": "object",
                        "layout": {
                            "shellSurface": "object_browser",
                            "visible": {
                                "objectWorkspacePanel": True,
                                "objectBrowserPanel": True,
                                "knowledgeConsolePanel": False,
                                "operationWorkspacePanel": False,
                                "knowledgeWorkspacePanel": False,
                                "workflowWorkspacePanel": False,
                            },
                        },
                    },
                    "source_registry": {
                        "activeSurface": "source_registry",
                        "activePane": "object",
                        "layout": {
                            "shellSurface": "source_registry",
                            "visible": {
                                "knowledgeConsolePanel": True,
                                "notebookWorkspacePanel": True,
                                "sourceRegistryPanel": True,
                                "workbenchTabs": False,
                                "workbenchLayout": False,
                            },
                        },
                    },
                    "verification_center": {
                        "activeSurface": "verification_center",
                        "activePane": "operation",
                        "layout": {
                            "shellSurface": "verification_center",
                            "visible": {
                                "operationWorkspacePanel": True,
                                "verificationReportPanel": True,
                                "mindmapStudioPanel": False,
                                "knowledgeConsolePanel": False,
                                "knowledgeWorkspacePanel": False,
                                "workflowWorkspacePanel": False,
                            },
                        },
                    },
                },
                "workbenchTabs": {
                    "workbenchTabObject": {"activePane": "object"},
                    "workbenchTabOperation": {"activePane": "operation"},
                    "workbenchTabKnowledge": {"activePane": "knowledge"},
                    "workbenchTabWorkflow": {"activePane": "workflow"},
                },
                "commandPane": {
                    "expandedAfterToggle": "true",
                    "navigatorExpandedBeforeCommand": "false",
                    "navigatorExpandedAfterToggle": "false",
                    "navigatorVisibleAfterToggle": False,
                    "panelHeightAfterToggle": 430,
                    "bodyHeightAfterToggle": 220,
                    "historyHeightAfterToggle": 170,
                },
                "notebookWorkspaceDetails": {
                    "expandedAfterToggle": "true",
                    "detailsVisibleAfterToggle": True,
                    "detailsHeightAfterToggle": 180,
                    "detailsScrollHeightAfterToggle": 220,
                },
                "notebookHeaderSpacing": {
                    "collapsed": {"topGap": 18, "rightGap": 18},
                    "expandedScrolled": {"topGap": 17, "rightGap": 19},
                    "topGapDelta": 1,
                    "rightGapDelta": 1,
                },
                "wideHeaderSpacing": {
                    "collapsed": {"topGap": 18, "rightGap": 18},
                    "expandedScrolled": {"topGap": 18, "rightGap": 18},
                    "topGapDelta": 0,
                    "rightGapDelta": 0,
                },
                "composerVisibility": {
                    "viewportWidth": 430,
                    "viewportHeight": 560,
                    "sendButtonVisibleInStress": True,
                    "sendButtonWithinViewportInStress": True,
                    "composerWithinViewportInStress": True,
                    "sendButtonRect": {"top": 480, "right": 420, "bottom": 540, "left": 350, "width": 70, "height": 60},
                    "composerRect": {"top": 470, "right": 430, "bottom": 552, "left": 0, "width": 430, "height": 82},
                },
                "workbenchScroll": {
                    "operation": {
                        "exists": True,
                        "visible": True,
                        "overflowY": "auto",
                        "clientHeight": 220,
                        "viewportClearance": {"topAfterTabs": 8, "bottomBeforeCommandPane": 8},
                        "contentBoundary": {
                            "firstFullyBelowHeader": True,
                            "lastFullyAboveCommandPane": True,
                        },
                    },
                    "knowledge": {
                        "exists": True,
                        "visible": True,
                        "overflowY": "auto",
                        "clientHeight": 220,
                        "viewportClearance": {"topAfterTabs": 8, "bottomBeforeCommandPane": 8},
                        "contentBoundary": {
                            "firstFullyBelowHeader": True,
                            "lastFullyAboveCommandPane": True,
                        },
                    },
                    "workflow": {
                        "exists": True,
                        "visible": True,
                        "overflowY": "auto",
                        "clientHeight": 220,
                        "viewportClearance": {"topAfterTabs": 8, "bottomBeforeCommandPane": 8},
                        "contentBoundary": {
                            "firstFullyBelowHeader": True,
                            "lastFullyAboveCommandPane": True,
                        },
                    },
                },
                "workspaceNavigator": {
                    "expandedState": "false",
                    "toggleVisible": False,
                    "gridVisible": False,
                    "expandedAfterSurfaceSelection": "false",
                },
                "workspaceSurfaceSelectFocus": {
                    "exists": True,
                    "focusedBeforeMousedown": True,
                    "blurredOnFocusedMousedown": True,
                    "activeSurfaceAfterChange": "mindmap_studio",
                    "blurredAfterChange": True,
                },
                "knowledgeMatrix": {"expandedAfterToggle": "true"},
                "settings": {
                    "opened": True,
                    "closed": True,
                    "contextScopeAutoPressed": True,
                    "layout": {
                        "exists": True,
                        "visible": True,
                        "headerVisible": True,
                        "returnButtonVisible": True,
                        "returnButtonWithinViewport": True,
                        "bodyOverflowY": "auto",
                        "bodyClientHeight": 360,
                        "topBoundary": {"firstVisibleAtTop": True},
                        "lastBoundary": {"lastVisibleAtBottom": True},
                    },
                },
                "history": {
                    "opened": True,
                    "closed": True,
                    "layout": {
                        "exists": True,
                        "visible": True,
                        "headerVisible": True,
                        "returnButtonVisible": True,
                        "returnButtonWithinViewport": True,
                        "bodyOverflowY": "auto",
                        "bodyClientHeight": 360,
                        "topBoundary": {"firstVisibleAtTop": True},
                        "lastBoundary": {"lastVisibleAtBottom": True},
                    },
                },
            }
        passing = module.check_browser_interaction_result(browser_result)
        self.assertEqual(passing["status"], "PASS", passing)

        top_clipped = copy.deepcopy(browser_result)
        top_clipped["settings"]["layout"]["topBoundary"]["firstVisibleAtTop"] = False
        top_clipped["settings"]["layout"]["topBoundary"]["firstId"] = "readinessPanel"
        top_clipped["settings"]["layout"]["topBoundary"]["firstTop"] = -2
        top_clipped["settings"]["layout"]["topBoundary"]["bodyTop"] = 92
        clipped_result = module.check_browser_interaction_result(top_clipped)
        self.assertEqual(clipped_result["status"], "FAIL")
        self.assertIn("settings page top content is clipped", "\n".join(clipped_result["problems"]))

        chat_not_filling = copy.deepcopy(browser_result)
        chat_not_filling["afterChat"]["layout"]["historyHeight"] = 112
        chat_not_filling["afterChat"]["layout"]["bodyHeight"] = 150
        chat_not_filling["afterChat"]["layout"]["composerBottomGap"] = 220
        chat_not_filling["afterChat"]["layout"]["historyFillsBody"] = False
        chat_not_filling["afterChat"]["layout"]["composerNearViewportBottom"] = False
        chat_layout_result = module.check_browser_interaction_result(chat_not_filling)
        self.assertEqual(chat_layout_result["status"], "FAIL")
        chat_layout_joined = "\n".join(chat_layout_result["problems"])
        self.assertIn("chat history did not fill available height", chat_layout_joined)
        self.assertIn("chat composer was not anchored near viewport bottom", chat_layout_joined)

        console_blank = copy.deepcopy(browser_result)
        console_blank["consoleLayout"]["blankGapAboveCommand"] = 260
        console_blank["consoleLayout"]["trailingBlankAboveCommand"] = 180
        console_blank["consoleLayout"]["fillsAboveCommand"] = False
        console_blank["consoleLayout"]["detailsNestedScrollTrap"] = True
        console_result = module.check_browser_interaction_result(console_blank)
        self.assertEqual(console_result["status"], "FAIL")
        console_joined = "\n".join(console_result["problems"])
        self.assertIn("console workspace leaves a blank gap above Command Pane", console_joined)
        self.assertIn("console workspace has excessive trailing blank space", console_joined)
        self.assertIn("notebook details became a nested scroll trap", console_joined)

        cramped_command_pane = copy.deepcopy(browser_result)
        cramped_command_pane["commandPane"]["navigatorExpandedAfterToggle"] = "true"
        cramped_command_pane["commandPane"]["navigatorVisibleAfterToggle"] = True
        cramped_command_pane["commandPane"]["panelHeightAfterToggle"] = 180
        cramped_command_pane["commandPane"]["historyHeightAfterToggle"] = 44
        command_result = module.check_browser_interaction_result(cramped_command_pane)
        self.assertEqual(command_result["status"], "FAIL")
        command_joined = "\n".join(command_result["problems"])
        self.assertIn("command pane expansion did not auto-collapse Workspace Navigator", command_joined)
        self.assertIn("Workspace Navigator remained visible while Command Pane was expanded", command_joined)
        self.assertIn("expanded Command Pane is too short", command_joined)
        self.assertIn("expanded conversation history is too short", command_joined)

        redundant_nav_visible = copy.deepcopy(browser_result)
        redundant_nav_visible["workspaceNavigator"]["toggleVisible"] = True
        redundant_nav_visible["workspaceNavigator"]["gridVisible"] = True
        redundant_nav_visible["workspaceNavigator"]["expandedState"] = "true"
        nav_result = module.check_browser_interaction_result(redundant_nav_visible)
        self.assertEqual(nav_result["status"], "FAIL")
        nav_joined = "\n".join(nav_result["problems"])
        self.assertIn("workspace navigator expand button should be hidden", nav_joined)
        self.assertIn("workspace navigator card grid should stay hidden", nav_joined)
        self.assertIn("workspace navigator expanded state should remain collapsed", nav_joined)

        select_focus_failed = copy.deepcopy(browser_result)
        select_focus_failed["workspaceSurfaceSelectFocus"]["blurredOnFocusedMousedown"] = False
        select_focus_result = module.check_browser_interaction_result(select_focus_failed)
        self.assertEqual(select_focus_result["status"], "FAIL")
        self.assertIn("workspace surface select kept focus on focused mousedown", "\n".join(select_focus_result["problems"]))

        missing_select_surface = copy.deepcopy(browser_result)
        missing_select_surface["workspaceSelectSurfaces"]["source_registry"]["layout"]["visible"]["sourceRegistryPanel"] = False
        missing_select_result = module.check_browser_interaction_result(missing_select_surface)
        self.assertEqual(missing_select_result["status"], "FAIL")
        self.assertIn("workspace select surface layout should show #sourceRegistryPanel", "\n".join(missing_select_result["problems"]))

        narrow_overflow = copy.deepcopy(browser_result)
        narrow_overflow["responsiveLayout"] = {
            "viewportWidth": 430,
            "badCount": 2,
            "badItems": [
                {
                    "selector": ".notebook-study-recommendation",
                    "id": "",
                    "className": "notebook-study-recommendation primary",
                    "clientWidth": 122,
                    "scrollWidth": 184,
                },
                {
                    "selector": ".notebook-runbook-action",
                    "id": "",
                    "className": "notebook-runbook-action primary",
                    "clientWidth": 54,
                    "scrollWidth": 86,
                },
            ],
        }
        narrow_result = module.check_browser_interaction_result(narrow_overflow)
        self.assertEqual(narrow_result["status"], "FAIL")
        self.assertIn("workspace narrow layout text overflow", "\n".join(narrow_result["problems"]))

        button_layout_issue = copy.deepcopy(browser_result)
        button_layout_issue["responsiveLayout"] = {
            "viewportWidth": 568,
            "badCount": 0,
            "buttonIssueCount": 2,
            "buttonIssues": [
                {
                    "type": "clipped",
                    "selector": ".topbar-actions .small-button",
                    "text": "新对话",
                    "clientWidth": 38,
                    "scrollWidth": 48,
                },
                {
                    "type": "outside-parent",
                    "selector": ".notebook-object-intake-action",
                    "text": "打开 Source Registry",
                    "parent": ".notebook-object-intake-route",
                },
            ],
        }
        button_result = module.check_browser_interaction_result(button_layout_issue)
        self.assertEqual(button_result["status"], "FAIL")
        self.assertIn("workspace narrow button layout issue", "\n".join(button_result["problems"]))

        header_spacing = copy.deepcopy(browser_result)
        header_spacing["notebookHeaderSpacing"] = {
            "collapsed": {"topGap": 18, "rightGap": 18},
            "expandedScrolled": {"topGap": 3, "rightGap": 18},
            "topGapDelta": 15,
            "rightGapDelta": 0,
        }
        header_spacing_result = module.check_browser_interaction_result(header_spacing)
        self.assertEqual(header_spacing_result["status"], "FAIL")
        self.assertIn("notebook workspace header spacing changed after expand", "\n".join(header_spacing_result["problems"]))

        wide_header_spacing = copy.deepcopy(browser_result)
        wide_header_spacing["wideHeaderSpacing"] = {
            "collapsed": {"topGap": 18, "rightGap": 18},
            "expandedScrolled": {"topGap": 5, "rightGap": 18},
            "topGapDelta": 13,
            "rightGapDelta": 0,
        }
        wide_header_spacing_result = module.check_browser_interaction_result(wide_header_spacing)
        self.assertEqual(wide_header_spacing_result["status"], "FAIL")
        self.assertIn(
            "notebook workspace wide header spacing changed after expand",
            "\n".join(wide_header_spacing_result["problems"]),
        )

        wide_button_whitespace = copy.deepcopy(browser_result)
        wide_button_whitespace["wideLayout"] = {
            "viewportWidth": 1280,
            "badCount": 0,
            "buttonIssueCount": 1,
            "buttonIssues": [
                {
                    "type": "excessive-bottom-gap",
                    "selector": ".notebook-object-task",
                    "text": "启动 workflow",
                    "bottomGap": 92,
                }
            ],
        }
        wide_button_result = module.check_browser_interaction_result(wide_button_whitespace)
        self.assertEqual(wide_button_result["status"], "FAIL")
        self.assertIn("workspace wide button layout issue", "\n".join(wide_button_result["problems"]))

        medium_button_overflow = copy.deepcopy(browser_result)
        medium_button_overflow["mediumLayout"] = {
            "viewportWidth": 840,
            "badCount": 1,
            "badItems": [
                {
                    "selector": ".mindmap-studio-actions",
                    "text": "读取现有脑图 预览 Diff 应用所选 验证事务 回滚事务",
                    "clientWidth": 520,
                    "scrollWidth": 612,
                }
            ],
            "buttonIssueCount": 1,
            "buttonIssues": [
                {
                    "type": "clipped",
                    "selector": "button",
                    "text": "读取现有脑图",
                    "clientWidth": 102,
                    "scrollWidth": 128,
                }
            ],
            "cardIssueCount": 0,
        }
        medium_button_result = module.check_browser_interaction_result(medium_button_overflow)
        self.assertEqual(medium_button_result["status"], "FAIL")
        self.assertIn("workspace medium button layout issue", "\n".join(medium_button_result["problems"]))
        self.assertIn("workspace medium layout text overflow", "\n".join(medium_button_result["problems"]))

        wide_card_sizing = copy.deepcopy(browser_result)
        wide_card_sizing["wideLayout"] = {
            "viewportWidth": 1280,
            "badCount": 0,
            "buttonIssueCount": 0,
            "cardIssueCount": 1,
            "cardIssues": [
                {
                    "type": "inconsistent-card-height",
                    "selector": ".notebook-object-intake-route",
                    "group": "notebookObjectIntakeRoutes",
                    "heights": [92, 92, 136, 136, 92, 136],
                }
            ],
        }
        wide_card_result = module.check_browser_interaction_result(wide_card_sizing)
        self.assertEqual(wide_card_result["status"], "FAIL")
        self.assertIn("workspace wide card layout issue", "\n".join(wide_card_result["problems"]))

        failing = module.check_browser_interaction_result({"initialMode": "workspace", "afterChat": {"mode": "workspace"}})
        self.assertEqual(failing["status"], "FAIL")
        joined = "\n".join(failing["problems"])
        self.assertIn("initial product mode is not chat", joined)
        self.assertIn("chat mode click did not switch product mode", joined)
        self.assertIn("workspace nav did not select", joined)
        self.assertIn("workspace surface layout", joined)
        self.assertIn("notebook workspace details toggle", joined)
        self.assertIn("knowledge matrix toggle", joined)
        self.assertIn("workbench tab did not activate", joined)

    def test_browser_action_stub_result_requires_expected_companion_actions(self) -> None:
        module = load_module()

        self.assertIn("agentPlanRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectRegistryScanButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectBrowserFilterButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectGraphRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectActivityRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("operationLedgerFilterButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("knowledgeWorkspaceSearchButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("mindmapTreeRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("mindmapStudioReadTreeButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("mindmapTargetRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("sendButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("newConversationButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("conversationHistoryAllButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("conversationHistoryObjectButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("contextScopeSelectionButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("contextScopeDocumentButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("saveFileSearchRootsButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("updateCheckButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("updateInstallButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("contextButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("permissionDiagnoseButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("openPermissionSettingsButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("cacheCurrentPdfButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("nativeCapabilitiesRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("uiFunctionalAcceptanceButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("notebookWorkspaceRunbookAutoButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("notebookWorkspaceRunbookContinueButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectGraphRelationAddButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectGraphRelationSaveButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("objectGraphRelationCancelButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("verificationRepairPlanRecommendedButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("realMnAcceptanceRunAllButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("singleDocumentAcceptanceButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("mainUiFunctionalAcceptanceButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("realMnAcceptanceSafeEvidenceButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("nativeHighlightWizardRetryButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("nativeHighlightWizardRefreshButton", module.BROWSER_ACTION_REQUIRED_BUTTONS)
        self.assertIn("agent_plan", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("request_mn_object_registry_scan", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("mn_read_tree", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("object_graph", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("object_activity", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("mindmap_target_status", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("notebook_runbook_preflight_record", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("object_graph_relation_save", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("request_mn_object_existence_probe", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("chat", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("conversation_new", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("settings_update", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("update_check", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("open_url", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("diagnose_permissions", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("open_full_disk_access_settings", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("request_pdf_cache", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("request_native_capability_probe", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("request_pdf_selection_probe", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("native_highlight_wizard_start", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("native_highlight_wizard_status", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("ui_functional_acceptance_summary", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertIn("knowledge_index_search", module.BROWSER_ACTION_REQUIRED_ACTIONS)
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["conversationHistoryAllButton"], "conversation_list")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["conversationHistoryObjectButton"], "conversation_list")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["objectBrowserFilterButton"], "object_browser")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["objectGraphRefreshButton"], "object_graph")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["objectActivityRefreshButton"], "object_activity")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["operationLedgerFilterButton"], "operation_ledger_list")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["knowledgeWorkspaceSearchButton"], "knowledge_index_search")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["mindmapTargetRefreshButton"], "mindmap_target_status")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["notebookWorkspaceRunbookAutoButton"], "notebook_runbook_preflight_record")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["notebookWorkspaceRunbookContinueButton"], "object_browser")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["objectGraphRelationSaveButton"], "object_graph_relation_save")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["verificationRepairPlanRecommendedButton"], "request_mn_object_existence_probe")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["realMnAcceptanceRunAllButton"], "single_document_acceptance_summary")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["singleDocumentAcceptanceButton"], "single_document_acceptance_summary")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["mainUiFunctionalAcceptanceButton"], "ui_functional_acceptance_summary")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["realMnAcceptanceSafeEvidenceButton"], "request_native_capability_probe")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["nativeHighlightWizardRetryButton"], "native_highlight_wizard_start")
        self.assertEqual(module.BROWSER_ACTION_BUTTON_ACTIONS["nativeHighlightWizardRefreshButton"], "request_pdf_selection_probe")
        self.assertIn("context", module.BROWSER_ACTION_REQUIRED_BRIDGE_ACTIONS)

        button_action_deltas = {button_id: 1 for button_id in module.BROWSER_ACTION_BUTTON_ACTIONS}
        button_action_deltas["realMnRuntimeSafeEvidenceButton"] = 1
        button_action_deltas["realMnRepair-refresh_native_capabilities"] = 1
        button_action_deltas["realMnRepair-run_native_highlight_wizard"] = 1
        passing = module.check_browser_action_stub_result(
            {
                "clicked": {
                    "agentPlanRefreshButton": True,
                    "sendButton": True,
                    "newConversationButton": True,
                    "conversationHistoryAllButton": True,
                    "conversationHistoryObjectButton": True,
                    "contextScopeSelectionButton": True,
                    "contextScopeDocumentButton": True,
                    "objectRegistryScanButton": True,
                    "objectBrowserFilterButton": True,
                    "objectGraphRefreshButton": True,
                    "objectActivityRefreshButton": True,
                    "operationLedgerFilterButton": True,
                    "knowledgeWorkspaceSearchButton": True,
                    "mindmapTreeRefreshButton": True,
                    "mindmapStudioReadTreeButton": True,
                    "mindmapTargetRefreshButton": True,
                    "notebookWorkspaceRefreshButton": True,
                    "notebookWorkspaceRunbookAutoButton": True,
                    "notebookWorkspaceRunbookContinueButton": True,
                    "objectBrowserRefreshButton": True,
                    "operationLedgerRefreshButton": True,
                    "verificationReportRefreshButton": True,
                    "settingsButton": True,
                    "saveFileSearchRootsButton": True,
                    "updateCheckButton": True,
                    "updateInstallButton": True,
                    "contextButton": True,
                    "permissionDiagnoseButton": True,
                    "openPermissionSettingsButton": True,
                    "cacheCurrentPdfButton": True,
                    "nativeCapabilitiesRefreshButton": True,
                    "healthCheckButton": True,
                    "aiBackendProbeButton": True,
                    "uiFunctionalAcceptanceButton": True,
                    "realMnRuntimeSafeEvidenceButton": True,
                    "realMnRepair-refresh_native_capabilities": True,
                    "realMnRepair-run_native_highlight_wizard": True,
                    "logsRefreshButton": True,
                    "conversationHistoryButton": True,
                    "objectGraphRelationAddButton": True,
                    "objectGraphRelationSaveButton": True,
                    "objectGraphRelationCancelButton": True,
                    "verificationRepairPlanRecommendedButton": True,
                    "realMnAcceptanceRunAllButton": True,
                    "singleDocumentAcceptanceButton": True,
                    "mainUiFunctionalAcceptanceButton": True,
                    "realMnAcceptanceSafeEvidenceButton": True,
                    "nativeHighlightWizardRetryButton": True,
                    "nativeHighlightWizardRefreshButton": True,
                },
                "actions": [
                    "agent_plan",
                    "chat",
                    "conversation_new",
                    "request_mn_object_registry_scan",
                    "mn_read_tree",
                    "object_graph",
                    "object_activity",
                    "mindmap_target_status",
                    "notebook_runbook_preflight_record",
                    "object_graph_relation_save",
                    "request_mn_object_existence_probe",
                    "notebook_workspace",
                    "object_browser",
                    "operation_ledger_list",
                    "verification_report_list",
                    "single_document_acceptance_summary",
                    "knowledge_index_search",
                    "settings_update",
                    "update_check",
                    "open_url",
                    "diagnose_permissions",
                    "open_full_disk_access_settings",
                    "request_pdf_cache",
                    "request_native_capability_probe",
                    "request_pdf_selection_probe",
                    "native_highlight_wizard_start",
                    "native_highlight_wizard_status",
                    "health",
                    "ai_backend_probe",
                    "ui_functional_acceptance_summary",
                    "logs_recent",
                    "conversation_list",
                ],
                "bridgeActions": ["context"],
                "connectionFailureVisible": False,
                "promptClearedAfterSend": True,
                "enterSubmitted": True,
                "contextScopeAfterClicks": "document",
                "buttonActionDeltas": button_action_deltas,
                "relationEditorOpened": True,
                "relationEditorClosedAfterCancel": True,
                "uiFunctionalLineText": "UI 功能验收：PASS / 11/11 / 阻塞 0",
                "uiFunctionalDetailText": "- PASS webview_browser_actions: WebView browser actions\n\n真实 MN4 运行态验收：BLOCK / 6/8 / 阻塞 2\n- BLOCK MN native API matrix：Missing nativeApiCapabilities event.\n  下一步：刷新 MN 能力。\n- BLOCK MN native visible highlight：Missing native visible highlight proof.\n  下一步：运行高亮采证。\n推荐修复：刷新 MN 能力 / 运行高亮采证",
                "finalUiState": {
                    "settingsHidden": True,
                    "historyHidden": True,
                    "activeProductMode": "workspace",
                    "commandPaneVisible": True,
                    "composerVisible": True,
                    "composerWithinViewport": True,
                    "sendButtonVisible": True,
                    "sendButtonWithinViewport": True,
                    "promptUsable": True,
                    "activeElementRepeatBlocking": False,
                    "activeElementId": "promptInput",
                },
            }
            )
        self.assertEqual(passing["status"], "PASS", passing)

        unstable = copy.deepcopy(passing["evidence"]["result"])
        unstable["finalUiState"]["historyHidden"] = False
        unstable["finalUiState"]["sendButtonWithinViewport"] = False
        unstable["finalUiState"]["activeElementRepeatBlocking"] = True
        unstable_result = module.check_browser_action_stub_result(unstable)
        self.assertEqual(unstable_result["status"], "FAIL")
        unstable_joined = "\n".join(unstable_result["problems"])
        self.assertIn("history page remained open after action sweep", unstable_joined)
        self.assertIn("send button was not usable after action sweep", unstable_joined)
        self.assertIn("focus remained on a repeat-blocking control", unstable_joined)

        failing = module.check_browser_action_stub_result(
            {
                "clicked": {"notebookWorkspaceRefreshButton": True},
                "actions": ["notebook_workspace"],
                "bridgeActions": [],
                "connectionFailureVisible": True,
                "promptClearedAfterSend": False,
                "enterSubmitted": False,
                "contextScopeAfterClicks": "auto",
                "buttonActionDeltas": {},
                "relationEditorOpened": False,
                "relationEditorClosedAfterCancel": False,
                "uiFunctionalLineText": "UI 功能验收：未运行",
                "uiFunctionalDetailText": "",
                "finalUiState": {
                    "settingsHidden": False,
                    "historyHidden": False,
                    "activeProductMode": "chat",
                    "commandPaneVisible": False,
                    "composerVisible": False,
                    "composerWithinViewport": False,
                    "sendButtonVisible": False,
                    "sendButtonWithinViewport": False,
                    "promptUsable": False,
                    "activeElementRepeatBlocking": True,
                    "activeElementId": "sendButton",
                },
            }
        )
        self.assertEqual(failing["status"], "FAIL")
        self.assertIn("missing backend action", "\n".join(failing["problems"]))
        self.assertIn("connection failure", "\n".join(failing["problems"]))
        self.assertIn("prompt input did not clear after send", "\n".join(failing["problems"]))
        self.assertIn("Enter key did not submit chat", "\n".join(failing["problems"]))
        self.assertIn("context scope did not switch to document", "\n".join(failing["problems"]))
        self.assertIn("missing native bridge action", "\n".join(failing["problems"]))
        self.assertIn("button did not trigger expected backend action", "\n".join(failing["problems"]))
        self.assertIn("object relation editor did not open", "\n".join(failing["problems"]))
        self.assertIn("object relation editor did not close after cancel", "\n".join(failing["problems"]))
        self.assertIn("UI functional acceptance result was not rendered as PASS", "\n".join(failing["problems"]))
        self.assertIn("UI functional acceptance detail did not render checks", "\n".join(failing["problems"]))
        self.assertIn("real MN4 runtime boundary was not rendered", "\n".join(failing["problems"]))
        self.assertIn("real MN4 runtime blockers were not rendered", "\n".join(failing["problems"]))
        self.assertIn("real MN4 recommended repairs were not rendered", "\n".join(failing["problems"]))
        self.assertIn("real MN4 recommended repair button was not clicked", "\n".join(failing["problems"]))
        self.assertIn("real MN4 recommended repair did not trigger native capability probe", "\n".join(failing["problems"]))
        self.assertIn("real MN4 highlight repair button was not clicked", "\n".join(failing["problems"]))
        self.assertIn("real MN4 highlight repair did not start highlight wizard", "\n".join(failing["problems"]))
        self.assertIn("settings page remained open after action sweep", "\n".join(failing["problems"]))
        self.assertIn("prompt input was not usable after action sweep", "\n".join(failing["problems"]))

    def test_browser_write_action_stub_result_requires_draft_transaction_and_bridge_actions(self) -> None:
        module = load_module()

        for target in ["mindmapStudioVerifyButton", "mindmapStudioRollbackButton"]:
            self.assertIn(target, module.BROWSER_WRITE_REQUIRED_CLICK_TARGETS)
        for action in [
            "generate_mindmap",
            "draft_save",
            "mindmap_diff_preview",
            "request_mindmap_diff_apply",
            "ai_edit_transaction_get",
            "ai_edit_transaction_verify",
            "request_mn_object_existence_probe",
            "review_queue_add",
        ]:
            self.assertIn(action, module.BROWSER_WRITE_REQUIRED_COMPANION_ACTIONS)
        for action in ["write_draft", "accept_ai_edit_transaction", "reject_ai_edit_transaction"]:
            self.assertIn(action, module.BROWSER_WRITE_REQUIRED_BRIDGE_ACTIONS)

        passing = module.check_browser_write_action_stub_result(
            {
                "clicked": {
                    "replyMindmapTreeButton": True,
                    "aiEditRejectButton": True,
                    "aiEditAcceptButton": True,
                    "aiEditReviewQueueButton": True,
                    "mindmapStudioPreviewDiffButton": True,
                    "mindmapStudioApplySelectedButton": True,
                    "mindmapStudioVerifyButton": True,
                    "mindmapStudioRollbackButton": True,
                    "transactionVerifyButton": True,
                    "transactionEvidenceButton": True,
                    "transactionProbeButton": True,
                },
                "actions": [
                    "generate_mindmap",
                    "draft_save",
                    "mindmap_diff_preview",
                    "request_mindmap_diff_apply",
                    "ai_edit_transaction_get",
                    "ai_edit_transaction_verify",
                    "request_mn_object_existence_probe",
                    "review_queue_add",
                ],
                "bridgeActions": [
                    "write_draft",
                    "accept_ai_edit_transaction",
                    "reject_ai_edit_transaction",
                ],
                "connectionFailureVisible": False,
                "finalUiState": {
                    "settingsHidden": True,
                    "historyHidden": True,
                    "activeProductMode": "workspace",
                    "commandPaneVisible": True,
                    "composerVisible": True,
                    "composerWithinViewport": True,
                    "sendButtonVisible": True,
                    "sendButtonWithinViewport": True,
                    "promptUsable": True,
                    "activeElementRepeatBlocking": False,
                    "activeElementId": "promptInput",
                },
            }
        )
        self.assertEqual(passing["status"], "PASS", passing)

        unstable = copy.deepcopy(passing["evidence"]["result"])
        unstable["finalUiState"]["promptUsable"] = False
        unstable["finalUiState"]["activeElementRepeatBlocking"] = True
        unstable["finalUiState"]["activeElementId"] = "mindmapStudioRollbackButton"
        unstable_result = module.check_browser_write_action_stub_result(unstable)
        self.assertEqual(unstable_result["status"], "FAIL")
        unstable_joined = "\n".join(unstable_result["problems"])
        self.assertIn("prompt input was not usable after write action sweep", unstable_joined)
        self.assertIn("focus remained on a repeat-blocking write control", unstable_joined)

        failing = module.check_browser_write_action_stub_result(
            {
                "clicked": {"replyMindmapTreeButton": True},
                "actions": ["generate_mindmap"],
                "bridgeActions": [],
                "connectionFailureVisible": True,
                "finalUiState": {
                    "settingsHidden": False,
                    "historyHidden": False,
                    "activeProductMode": "chat",
                    "commandPaneVisible": False,
                    "composerVisible": False,
                    "composerWithinViewport": False,
                    "sendButtonVisible": False,
                    "sendButtonWithinViewport": False,
                    "promptUsable": False,
                    "activeElementRepeatBlocking": True,
                    "activeElementId": "mindmapStudioRollbackButton",
                },
            }
        )
        self.assertEqual(failing["status"], "FAIL")
        joined = "\n".join(failing["problems"])
        self.assertIn("missing write backend action", joined)
        self.assertIn("missing native bridge action", joined)
        self.assertIn("connection failure", joined)
        self.assertIn("settings page remained open after write action sweep", joined)
        self.assertIn("send button was not usable after write action sweep", joined)


if __name__ == "__main__":
    unittest.main()
