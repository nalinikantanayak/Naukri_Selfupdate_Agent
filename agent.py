import json
import logging
import os
import smtplib
import time

from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from playwright.sync_api import sync_playwright


# ==================================================
# PATH CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).parent

PROFILE_PATH = BASE_DIR / "browser_profile"
STATE_FILE = BASE_DIR / "state.json"
CONTENT_FILE = BASE_DIR / "content.json"

LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = BASE_DIR / "screenshots"

PROFILE_URL = "https://www.naukri.com/mnjuser/profile?id=&altresid"

LOG_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR.mkdir(exist_ok=True)


# ==================================================
# RETRY CONFIGURATION
# ==================================================

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 20


# ==================================================
# GMAIL CONFIGURATION
# ==================================================

GMAIL_SENDER = os.getenv("NAUKRI_AGENT_EMAIL")
GMAIL_RECEIVER = "rcnayak456@gmail.com"
GMAIL_APP_PASSWORD = os.getenv("NAUKRI_AGENT_APP_PASSWORD")


# ==================================================
# LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    filename=LOG_DIR / "agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def log(message):
    print(message)
    logging.info(message)


# ==================================================
# SEND EMAIL NOTIFICATION
# ==================================================

def send_email(subject, body):

    try:

        if not GMAIL_SENDER:

            log(
                "EMAIL ERROR: "
                "NAUKRI_AGENT_EMAIL environment variable "
                "was not found."
            )

            return False

        if not GMAIL_APP_PASSWORD:

            log(
                "EMAIL ERROR: "
                "NAUKRI_AGENT_APP_PASSWORD environment variable "
                "was not found."
            )

            return False

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = GMAIL_SENDER
        message["To"] = GMAIL_RECEIVER

        message.set_content(body)

        log("Sending email notification...")

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as smtp:

            smtp.login(
                GMAIL_SENDER,
                GMAIL_APP_PASSWORD
            )

            smtp.send_message(message)

        log(
            "Email notification sent successfully."
        )

        return True

    except Exception as e:

        log(
            f"EMAIL ERROR: {str(e)}"
        )

        return False


# ==================================================
# LOAD STATE
# ==================================================

def load_state():

    default_state = {
        "last_successful_morning_update": None,
        "last_successful_afternoon_update": None,
        "last_run_status": "NOT_STARTED",
        "last_run_time": None,
        "last_headline_index": -1,
        "message": ""
    }

    if not STATE_FILE.exists():

        return default_state

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            state = json.load(file)

    except Exception:

        log(
            "WARNING: Could not read state.json. "
            "Using default state."
        )

        return default_state

    for key, value in default_state.items():

        if key not in state:

            state[key] = value

    return state


# ==================================================
# SAVE STATE
# ==================================================

def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )


# ==================================================
# LOAD RESUME HEADLINES
# ==================================================

def load_headlines():

    with open(
        CONTENT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = json.load(file)

    headlines = content.get(
        "resume_headlines",
        []
    )

    if not headlines:

        raise Exception(
            "No resume headlines found in content.json"
        )

    return headlines


# ==================================================
# GET CURRENT UPDATE SLOT
# ==================================================

def get_time_slot():

    now = datetime.now()

    current_minutes = (
        now.hour * 60
        + now.minute
    )

    # ----------------------------------------------
    # MORNING SLOT
    # 08:50 AM - 08:59 AM
    # ----------------------------------------------

    morning_start = (
        8 * 60
        + 50
    )

    morning_end = (
        9 * 60
    )

    if (
        morning_start
        <= current_minutes
        < morning_end
    ):

        return "morning"

    # ----------------------------------------------
    # AFTERNOON SLOT
    # 03:45 PM - 03:54 PM
    # ----------------------------------------------

    afternoon_start = (
        15 * 60
        + 45
    )

    afternoon_end = (
        15 * 60
        + 55
    )

    if (
        afternoon_start
        <= current_minutes
        < afternoon_end
    ):

        return "afternoon"

    return None


# ==================================================
# CHECK DUPLICATE UPDATE
# ==================================================

def already_updated_for_slot(
    state,
    slot
):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    if slot == "morning":

        return (
            state.get(
                "last_successful_morning_update"
            )
            == today
        )

    if slot == "afternoon":

        return (
            state.get(
                "last_successful_afternoon_update"
            )
            == today
        )

    return False


# ==================================================
# MARK SLOT AS SUCCESSFUL
# ==================================================

def mark_slot_success(
    state,
    slot
):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    if slot == "morning":

        state[
            "last_successful_morning_update"
        ] = today

    elif slot == "afternoon":

        state[
            "last_successful_afternoon_update"
        ] = today


# ==================================================
# GET NEXT HEADLINE
# ==================================================

def get_next_headline(
    state,
    headlines
):

    last_index = state.get(
        "last_headline_index",
        -1
    )

    next_index = (
        last_index + 1
    ) % len(headlines)

    return (
        headlines[next_index],
        next_index
    )


# ==================================================
# SAVE FAILURE SCREENSHOT
# ==================================================

def save_failure_screenshot(page):

    if page is None:

        return

    try:

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        screenshot_file = (
            SCREENSHOT_DIR
            / f"failure_{timestamp}.png"
        )

        page.screenshot(
            path=str(screenshot_file),
            full_page=True
        )

        log(
            f"Failure screenshot saved: "
            f"{screenshot_file}"
        )

    except Exception as screenshot_error:

        log(
            f"Could not save failure screenshot: "
            f"{screenshot_error}"
        )


# ==================================================
# CHECK NAUKRI LOGIN STATUS
# ==================================================

def check_login_status(page):

    current_url = page.url.lower()

    log(
        f"Current page URL: "
        f"{page.url}"
    )

    login_url_keywords = [
        "login",
        "signin",
        "auth"
    ]

    for keyword in login_url_keywords:

        if keyword in current_url:

            raise Exception(
                "LOGIN REQUIRED: "
                "Your Naukri session appears "
                "to have expired."
            )

    password_fields = page.locator(
        "input[type='password']"
    )

    if password_fields.count() > 0:

        raise Exception(
            "LOGIN REQUIRED: "
            "A password field was detected."
        )

    log(
        "Saved Naukri session appears to be active."
    )


# ==================================================
# PERFORM PROFILE UPDATE
# ==================================================

def perform_profile_update():

    state = load_state()

    # ----------------------------------------------
    # CHECK SCHEDULE WINDOW
    # ----------------------------------------------

    slot = get_time_slot()

    if slot is None:

        current_time = datetime.now().strftime(
            "%I:%M %p"
        )

        log(
            f"Current time: {current_time}"
        )

        log(
            "No scheduled update slot is active."
        )

        log(
            "Agent is exiting without updating "
            "the Naukri profile."
        )

        return {
            "status": "SKIPPED",
            "reason": "OUTSIDE_SCHEDULE"
        }

    log(
        f"Current update slot: "
        f"{slot.upper()}"
    )

    # ----------------------------------------------
    # PREVENT DUPLICATE UPDATE
    # ----------------------------------------------

    if already_updated_for_slot(
        state,
        slot
    ):

        log(
            f"{slot.capitalize()} update "
            "already completed today."
        )

        return {
            "status": "SKIPPED",
            "reason": "ALREADY_COMPLETED",
            "slot": slot
        }

    # ----------------------------------------------
    # LOAD HEADLINES
    # ----------------------------------------------

    headlines = load_headlines()

    new_headline, new_index = (
        get_next_headline(
            state,
            headlines
        )
    )

    # ============================================================
    # VALIDATE RESUME HEADLINE LENGTH
    # ============================================================

    MAX_HEADLINE_LENGTH = 250

    if len(new_headline) > MAX_HEADLINE_LENGTH:
        raise Exception(
            f"Resume headline exceeds Naukri's 250-character limit. "
            f"Length: {len(new_headline)} characters."
        )

    log(
        f"Selected headline version: "
        f"{new_index + 1}"
    )

    log(
        f"Headline length: "
        f"{len(new_headline)} characters"
    )

    context = None
    page = None

    with sync_playwright() as p:

        try:

            # ------------------------------------------
            # OPEN BROWSER
            # ------------------------------------------

            log(
                "Opening browser using saved session..."
            )

            context = (
                p.chromium.launch_persistent_context(
                    user_data_dir=str(
                        PROFILE_PATH
                    ),
                    headless=False
                )
            )

            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            # ------------------------------------------
            # OPEN NAUKRI PROFILE
            # ------------------------------------------

            log(
                "Opening Naukri profile..."
            )

            page.goto(
                PROFILE_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                3000
            )

            check_login_status(page)

            log(
                "Naukri profile opened successfully."
            )

            # ------------------------------------------
            # FIND RESUME HEADLINE SECTION
            # ------------------------------------------

            headline_card = page.locator(
                "div.resumeHeadline"
            )

            headline_card.wait_for(
                state="visible",
                timeout=30000
            )

            log(
                "Resume Headline section found."
            )

            # ------------------------------------------
            # CLICK EDIT ICON
            # ------------------------------------------

            edit_button = headline_card.locator(
                "span.edit.icon"
            )

            edit_button.wait_for(
                state="visible",
                timeout=10000
            )

            log(
                "Clicking Resume Headline edit icon..."
            )

            edit_button.click()

            # ------------------------------------------
            # WAIT FOR EDITOR
            # ------------------------------------------

            textarea = page.locator(
                "textarea.ge__text-area"
            )

            textarea.wait_for(
                state="visible",
                timeout=15000
            )

            current_headline = (
                textarea.input_value()
            )

            log(
                f"Current headline: "
                f"{current_headline}"
            )

            # ------------------------------------------
            # CHECK IF SELECTED HEADLINE
            # IS ALREADY ACTIVE
            # ------------------------------------------

            if (
                current_headline.strip()
                == new_headline.strip()
            ):

                log(
                    "Selected headline is already active."
                )

                new_index = (
                    new_index + 1
                ) % len(headlines)

                new_headline = (
                    headlines[new_index]
                )

            log(
                f"Updating to headline version: "
                f"{new_index + 1}"
            )

            # ------------------------------------------
            # UPDATE HEADLINE
            # ------------------------------------------

            textarea.fill(
                new_headline
            )

            # ------------------------------------------
            # CLICK SAVE
            # ------------------------------------------

            save_button = page.get_by_role(
                "button",
                name="Save",
                exact=True
            )

            save_button.wait_for(
                state="visible",
                timeout=10000
            )

            log(
                "Clicking Save..."
            )

            save_button.click()

            # ------------------------------------------
            # WAIT FOR SAVE OPERATION
            # ------------------------------------------

            log(
                "Waiting for Naukri to save the headline..."
    )

            page.wait_for_timeout(
                5000
            )

            # ------------------------------------------
            # CHECK HEADLINE BEFORE REFRESH
            # ------------------------------------------

            log(
                "Checking headline after Save before refresh..."
            )

            headline_card = page.locator(
                "div.resumeHeadline"
            )

            headline_card.wait_for(
                state="visible",
                timeout=30000
            )

            saved_text_before_refresh = (
                headline_card.inner_text()
            )

            if new_headline.strip() in saved_text_before_refresh:
                log(
                    "Headline appears updated before refresh."
                )
            else:
                log(
                    "Headline not detected before refresh. "
                    "Continuing with refresh verification..."
                )

            # ------------------------------------------
            # REFRESH PROFILE
            # ------------------------------------------

            log(
                "Refreshing profile to verify "
                "saved headline..."
            )

            page.reload(
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(
                5000
            )

            check_login_status(page)

            # ------------------------------------------
            # VERIFY UPDATED HEADLINE
            # ------------------------------------------

            headline_card = page.locator(
                "div.resumeHeadline"
            )

            headline_card.wait_for(
                state="visible",
                timeout=30000
            )

            updated_text = (
                headline_card.inner_text()
            )

            if (
                new_headline.strip()
                not in updated_text
            ):

                raise Exception(
                    "Updated headline was not found "
                    "after refreshing the profile."
                )

            log(
                "Updated headline verified successfully."
            )

            # ------------------------------------------
            # UPDATE STATE
            # ------------------------------------------

            mark_slot_success(
                state,
                slot
            )

            state[
                "last_run_status"
            ] = "SUCCESS"

            state[
                "last_run_time"
            ] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            state[
                "last_headline_index"
            ] = new_index

            state[
                "message"
            ] = (
                f"{slot.capitalize()} profile update "
                "completed successfully"
            )

            save_state(state)

            log(
                f"{slot.capitalize()} update "
                "completed successfully."
            )

            # ------------------------------------------
            # RETURN COMPLETE SUCCESS DETAILS
            # ------------------------------------------

            return {
                "status": "SUCCESS",
                "slot": slot,
                "headline": new_headline,
                "headline_version": new_index + 1
            }

        except Exception as e:

            error_message = str(e)

            log(
                f"ERROR: {error_message}"
            )

            save_failure_screenshot(
                page
            )

            # ------------------------------------------
            # LOGIN REQUIRED
            # ------------------------------------------

            if (
                "LOGIN REQUIRED:"
                in error_message
            ):

                state[
                    "last_run_status"
                ] = "LOGIN_REQUIRED"

                state[
                    "last_run_time"
                ] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                state[
                    "message"
                ] = error_message

                save_state(state)

                return {
                    "status": "LOGIN_REQUIRED",
                    "error": error_message
                }

            # ------------------------------------------
            # NORMAL FAILURE
            # ------------------------------------------

            return {
                "status": "FAILED",
                "error": error_message
            }

        finally:

            if context:

                log(
                    "Closing browser safely..."
                )

                context.close()


# ==================================================
# MAIN AGENT
# ==================================================

def run_agent():

    log("=" * 60)
    log("NAUKRI DAILY PROFILE AGENT STARTED")
    log("=" * 60)

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        log(
            f"Attempt "
            f"{attempt}/{MAX_ATTEMPTS}"
        )

        result = perform_profile_update()

        status = result.get("status")

        # ----------------------------------------------
        # SKIPPED
        # ----------------------------------------------

        if status == "SKIPPED":

            reason = result.get(
                "reason"
            )

            if reason == "OUTSIDE_SCHEDULE":

                log(
                    "Agent skipped because the current "
                    "time is outside the scheduled "
                    "update window."
                )

            elif reason == "ALREADY_COMPLETED":

                slot = result.get(
                    "slot",
                    ""
                ).upper()

                log(
                    f"{slot} update was already "
                    "completed today."
                )

                log(
                    "No email will be sent because "
                    "no new profile update was made."
                )

            return

        # ----------------------------------------------
        # SUCCESS
        # ----------------------------------------------

        if status == "SUCCESS":

            log(
                "Agent completed successfully."
            )

            update_slot = result[
                "slot"
            ].upper()

            headline = result[
                "headline"
            ]

            headline_version = result[
                "headline_version"
            ]

            current_time = datetime.now().strftime(
                "%Y-%m-%d %I:%M:%S %p"
            )

            # ------------------------------------------
            # SEND DETAILED SUCCESS EMAIL
            # ------------------------------------------

            send_email(
                (
                    "Naukri Profile Update Successful "
                    f"- {update_slot}"
                ),

                (
                    "NAUKRI DAILY PROFILE AGENT REPORT\n"
                    "====================================\n\n"

                    "Status: SUCCESS\n"

                    f"Update Slot: {update_slot}\n"

                    f"Date & Time: "
                    f"{current_time}\n\n"

                    f"Headline Version: "
                    f"{headline_version}\n\n"

                    "Updated Resume Headline:\n"
                    "------------------------------------\n"

                    f"{headline}\n\n"

                    "Verification:\n"

                    "SUCCESS - The Naukri profile was "
                    "refreshed after saving and the "
                    "updated Resume Headline was "
                    "verified successfully.\n\n"

                    "Naukri Daily Profile Agent"
                )
            )

            return

        # ----------------------------------------------
        # LOGIN REQUIRED
        # ----------------------------------------------

        if status == "LOGIN_REQUIRED":

            log(
                "Agent stopped because manual "
                "login is required."
            )

            send_email(
                "ACTION REQUIRED: Naukri Login Expired",

                (
                    "NAUKRI DAILY PROFILE AGENT ALERT\n"
                    "====================================\n\n"

                    "Status: LOGIN REQUIRED\n\n"

                    "Your Naukri Daily Profile Agent "
                    "could not continue because the "
                    "saved Naukri login session appears "
                    "to have expired.\n\n"

                    "ACTION REQUIRED:\n"

                    "Please manually open the browser "
                    "profile used by this agent and "
                    "log in to Naukri again.\n\n"

                    f"Detected at: "
                    f"{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n\n"

                    "Naukri Daily Profile Agent"
                )
            )

            return

        # ----------------------------------------------
        # RETRY FAILED ATTEMPT
        # ----------------------------------------------

        if status == "FAILED":

            log(
                f"Attempt {attempt} failed."
            )

            if attempt < MAX_ATTEMPTS:

                log(
                    f"Retrying in "
                    f"{RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    # ==================================================
    # ALL RETRIES FAILED
    # ==================================================

    state = load_state()

    state[
        "last_run_status"
    ] = "FAILED"

    state[
        "last_run_time"
    ] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    state[
        "message"
    ] = (
        f"Agent failed after "
        f"{MAX_ATTEMPTS} attempts"
    )

    save_state(state)

    log(
        "Agent failed after all retry attempts."
    )

    send_email(
        "ALERT: Naukri Profile Agent Failed",

        (
            "NAUKRI DAILY PROFILE AGENT ALERT\n"
            "====================================\n\n"

            "Status: FAILED\n\n"

            f"The agent failed after "
            f"{MAX_ATTEMPTS} attempts.\n\n"

            f"Time: "
            f"{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n\n"

            "Please check:\n"

            f"Log file: "
            f"{LOG_DIR / 'agent.log'}\n\n"

            "Also check the screenshots folder "
            "for failure screenshots.\n\n"

            "Naukri Daily Profile Agent"
        )
    )


# ==================================================
# START AGENT
# ==================================================

if __name__ == "__main__":

    run_agent()