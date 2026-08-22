import json
import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "browser_profile"
STATE_FILE = BASE_DIR / "state.json"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    filename=LOG_DIR / "agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def log(message):
    print(message)
    logging.info(message)


# --------------------------------------------------
# LOAD AGENT MEMORY
# --------------------------------------------------

def load_state():

    if not STATE_FILE.exists():
        return {
            "last_successful_update": None,
            "last_run_status": "NOT_STARTED",
            "last_run_time": None,
            "message": ""
        }

    with open(STATE_FILE, "r") as file:
        return json.load(file)


# --------------------------------------------------
# SAVE AGENT MEMORY
# --------------------------------------------------

def save_state(state):

    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=4)


# --------------------------------------------------
# CHECK IF ALREADY UPDATED TODAY
# --------------------------------------------------

def already_updated_today(state):

    today = datetime.now().strftime("%Y-%m-%d")

    return state.get("last_successful_update") == today


# --------------------------------------------------
# MAIN AGENT
# --------------------------------------------------

def run_agent():

    log("=" * 60)
    log("NAUKRI DAILY PROFILE AGENT STARTED")
    log("=" * 60)

    state = load_state()

    # Prevent duplicate successful runs
    if already_updated_today(state):

        log("Today's profile update was already completed.")
        log("Agent will exit safely.")

        return

    # ----------------------------------------------
    # START PLAYWRIGHT
    # ----------------------------------------------

    with sync_playwright() as p:

        context = None

        try:

            log("Opening browser using saved session...")

            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_PATH),
                headless=False
            )

            # Get existing page or create a new one
            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            log("Opening Naukri...")

            page.goto(
                "https://www.naukri.com/",
                wait_until="domcontentloaded",
                timeout=60000
            )

            log("Naukri page opened successfully.")

            # -----------------------------------------
            # FUTURE PROFILE UPDATE ACTION
            # WILL GO HERE
            # -----------------------------------------

            log("Agent test run completed successfully.")

            state["last_run_status"] = "SUCCESS"

            state["last_run_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            state["message"] = "Browser session test successful"

            save_state(state)

            log("Agent state saved.")

        except Exception as e:

            error_message = str(e)

            log(f"ERROR: {error_message}")

            state["last_run_status"] = "FAILED"

            state["last_run_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            state["message"] = error_message

            save_state(state)

        finally:

            if context:

                log("Closing browser safely...")
                context.close()

            log("Agent finished.")


# --------------------------------------------------
# START AGENT
# --------------------------------------------------

if __name__ == "__main__":
    run_agent()