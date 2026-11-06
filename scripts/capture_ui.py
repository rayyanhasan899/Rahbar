"""Capture the actual browser UI and its real API response, never a mock image."""
from pathlib import Path
import json
import shutil
from playwright.sync_api import sync_playwright


def main() -> None:
    out = Path(__file__).resolve().parents[1] / ".venv" / "acceptance"
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    with sync_playwright() as p:
        executable = shutil.which("google-chrome") or shutil.which("chromium")
        if not executable:
            raise RuntimeError("a real Chromium browser is required for UI evidence")
        browser = p.chromium.launch(executable_path=executable, args=["--no-sandbox", "--no-proxy-server", "--host-resolver-rules=MAP rahbar.local 127.0.0.1"])
        page = browser.new_page(viewport={"width": 1400, "height": 1050})
        page.goto("http://rahbar.local:18080/", wait_until="networkidle")
        page.locator("#question").fill("What is the medium of instruction and examinations for most courses?")
        with page.expect_response(lambda r: r.url.endswith("/api/ask"), timeout=300000) as reply:
            page.locator("#send").click()
        response = reply.value
        data = response.json()
        page.locator("article.a:not(.pending)").wait_for()
        page.screenshot(path=str(out / "real-ui.png"), full_page=True)
        out.joinpath("real-ui-response.json").write_text(json.dumps(data, indent=2))
        out.joinpath("real-ui-browser.txt").write_text(browser.version)
        browser.close()
        assert response.status == 200 and data["provider"] == "ollama"
        assert data["answered_from_context"] and data["citations"], data


if __name__ == "__main__":
    main()
