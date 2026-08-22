from playwright.sync_api import sync_playwright

PROFILE_PATH = "./browser_profile"


def main():
    with sync_playwright() as p:
        context = None

        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_PATH,
                headless=False
            )

            page = context.pages[0] if context.pages else context.new_page()

            page.goto(
                "https://www.naukri.com/",
                wait_until="domcontentloaded"
            )

            print("Browser opened using saved session.")
            input("Check whether you are already logged in, then press ENTER...")

        except Exception as e:
            print(f"\nERROR: {e}")

        finally:
            if context:
                print("Closing browser safely...")
                context.close()


if __name__ == "__main__":
    main()