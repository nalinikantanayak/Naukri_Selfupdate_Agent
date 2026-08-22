from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "browser_profile"


def main():

    with sync_playwright() as p:

        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_PATH),
            headless=False
        )

        try:

            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            print("\nOpening Naukri...")

            page.goto(
                "https://www.naukri.com/",
                wait_until="domcontentloaded",
                timeout=60000
            )

            print("Page opened successfully.")
            print(f"Current URL: {page.url}")

            print("\n" + "=" * 70)
            print("PAGE LINKS")
            print("=" * 70)

            links = page.locator("a").all()

            for index, link in enumerate(links[:100], start=1):

                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute("href")

                    if text:
                        print(
                            f"{index}. TEXT: {text[:80]} | HREF: {href}"
                        )

                except Exception:
                    pass

            print("\n" + "=" * 70)
            print("BUTTONS")
            print("=" * 70)

            buttons = page.locator("button").all()

            for index, button in enumerate(buttons[:100], start=1):

                try:
                    text = button.inner_text().strip()

                    if text:
                        print(
                            f"{index}. BUTTON: {text[:100]}"
                        )

                except Exception:
                    pass

            print("\n" + "=" * 70)
            print("INPUT FIELDS")
            print("=" * 70)

            inputs = page.locator("input").all()

            for index, item in enumerate(inputs[:50], start=1):

                try:
                    name = item.get_attribute("name")
                    placeholder = item.get_attribute("placeholder")
                    input_type = item.get_attribute("type")

                    print(
                        f"{index}. "
                        f"type={input_type}, "
                        f"name={name}, "
                        f"placeholder={placeholder}"
                    )

                except Exception:
                    pass

            print("\nInspection completed.")
            print("Browser will remain open for manual inspection.")

            input(
                "\nPlease inspect the page manually. "
                "When finished, press ENTER to close..."
            )

        finally:

            print("Closing browser...")
            context.close()


if __name__ == "__main__":
    main()