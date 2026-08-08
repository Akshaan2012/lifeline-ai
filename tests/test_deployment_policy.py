from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentPolicyTests(unittest.TestCase):
    def test_dependencies_are_reproducibly_pinned_and_exclude_compromised_translator(self) -> None:
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        self.assertTrue(requirements)
        self.assertTrue(all("==" in line for line in requirements if line.strip()))
        self.assertFalse(any("deep-translator" in line.lower() for line in requirements))
        source = (ROOT / "backend" / "translator.py").read_text(encoding="utf-8")
        self.assertNotIn("deep_translator", source)

    def test_public_app_link_uses_the_deployed_unique_slug(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "https://lifeline-ai-jwp5bk2k67r3jygxlgix2k.streamlit.app",
            readme,
        )
        self.assertNotIn("https://lifeline-ai.streamlit.app", readme)

    def test_sidebar_is_expanded_and_has_no_collapse_control(self) -> None:
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('initial_sidebar_state="expanded"', source)
        self.assertIn('[data-testid="stSidebar"][aria-expanded="false"]', source)
        self.assertIn('[data-testid="stSidebarCollapseButton"]', source)
        persistent_rules = source[source.index("/* Patient navigation is intentionally persistent. */"):]
        self.assertIn("display: none !important", persistent_rules)
        self.assertIn("pointer-events: none !important", persistent_rules)

    def test_quiz_radios_do_not_preselect_an_answer(self) -> None:
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        challenge = source[source.index("def render_challenge()") : source.index("def render_safety_videos()")]
        self.assertIn("index=None", challenge)


if __name__ == "__main__":
    unittest.main()