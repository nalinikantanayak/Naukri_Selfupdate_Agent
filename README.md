#Naukri Agent
# Naukri Self-Update Agent

An automated Python-based profile management agent that updates the Naukri Resume Headline using Playwright and a persistent browser session.

The agent is designed to run automatically on Windows using Task Scheduler and provides email notifications for successful updates, login/session expiry, and failures.

---

## 🚀 Project Overview

The Naukri Self-Update Agent automates the repetitive task of keeping a Naukri Resume Headline updated.

The agent:

- Opens the Naukri profile using a saved Playwright browser session
- Identifies the Resume Headline section
- Selects the next headline from `content.json`
- Updates the Resume Headline
- Saves the change
- Refreshes the profile
- Verifies that the new headline was successfully updated
- Maintains execution state using `state.json`
- Prevents duplicate updates within the same scheduled slot
- Sends Gmail notifications for success, login expiry, and failures
- Retries failed operations up to three times
- Runs automatically through Windows Task Scheduler

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │ Windows Task Scheduler│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    run_agent.bat     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      agent.py        │
                    │                      │
                    │ Scheduling            │
                    │ Retry handling        │
                    │ Login detection       │
                    │ Profile update        │
                    │ Verification          │
                    │ Email notification    │
                    └───────┬───────┬──────┘
                            │       │
                ┌───────────┘       └────────────┐
                ▼                                ▼
      ┌──────────────────┐             ┌──────────────────┐
      │   content.json   │             │ browser_profile/ │
      │                  │             │                  │
      │ Resume Headlines │             │ Playwright       │
      │                  │             │ persistent       │
      └──────────────────┘             │ session          │
                                       └──────────────────┘
                                                │
                                                ▼
                                      ┌──────────────────┐
                                      │      Naukri      │
                                      │     Profile      │
                                      └──────────────────┘

                            ┌──────────────────┐
                            │      Gmail       │
                            │ Email Alerts     │
                            └──────────────────┘