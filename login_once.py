from playwright.sync_api import sync_playwright

PROFILE_PATH = "./browser_profile"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )

        page = browser.new_page()

        page.goto(
            "https://www.naukri.com/",
            wait_until="domcontentloaded"
        )

        print("\n" + "=" * 60)
        print("NAUKRI LOGIN SESSION SETUP")
        print("=" * 60)
        print("Please log in to your Naukri account manually.")
        print("Complete OTP/CAPTCHA if Naukri asks for it.")
        print()
        input("After successful login, press ENTER here...")

        print("Saving browser session...")
        browser.close()

        print("Session saved successfully!")
        print("You can now use this session in future agent runs.")


if __name__ == "__main__":
    main()