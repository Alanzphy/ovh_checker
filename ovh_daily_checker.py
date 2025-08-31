import os, re, asyncio
import requests
from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    TimeoutError as PWTimeoutError,
    expect,
)

# === Config ===
URL = "https://www.ovhcloud.com/en/vps/configurator/"
TIMEOUT = 30000  # Increased to 30s
load_dotenv()
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BOT = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT = os.getenv("TELEGRAM_CHAT_ID", "")


def notify(msg: str):
    print(f"Notifying: {msg}")
    if BOT and CHAT:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT}/sendMessage",
                json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"Error notifying Telegram: {e}")
    else:
        print("Telegram bot not configured. Showing notification in console.")


async def accept_cookies(page):
    try:
        cookie_btn = page.get_by_role("button", name=re.compile("accept all", re.I))
        if await cookie_btn.count() > 0:
            await cookie_btn.first.click(timeout=2000)
            await page.wait_for_timeout(500)
    except Exception:
        pass  # If no cookies, no problem


async def click_and_verify(page, selector, name, force=False):
    """Locates, clicks an element and verifies it becomes selected."""
    try:
        print(f"Attempting to click '{name}' with selector '{selector}'...")
        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=10000)

        if force:
            await element.click(force=True, timeout=5000)
        else:
            await element.click(timeout=5000)

        print(f"✅ Successful click on '{name}'. Verifying it's selected...")

        # For label elements, verify if the associated input is checked
        try:
            # Get the 'for' attribute of the label to find the input
            for_attr = await element.get_attribute("for")
            if for_attr:
                input_element = page.locator(f"input[id='{for_attr}']")
                await expect(input_element).to_be_checked(timeout=5000)
                print(f"✅ '{name}' confirmed as selected.")
            else:
                # If it's not a label, try to verify data-state
                await expect(element).to_have_attribute(
                    "data-state", "checked", timeout=5000
                )
                print(f"✅ '{name}' confirmed as selected.")
        except:
            # If verification fails, we still consider the click successful
            print(f"⚠️ '{name}' - click performed but couldn't verify state.")

        await page.wait_for_timeout(2000)  # Longer pause for UI to update
        return True
    except PWTimeoutError:
        print(
            f"⚠️ Timeout waiting for '{name}' to be visible/enabled. It may not be present on the page."
        )
    except Exception as e:
        print(f"❌ Error clicking '{name}' or verifying selection: {e}")

    return False


async def check_availability(page, region_name, location_name, location_code):
    """
    Checks server availability in a specific region and location.
    """
    try:
        # 1. Navigate to the region tab (Europe or North America)
        print(f"\nNavigating to '{region_name}' tab...")
        region_selector = (
            f"button[role='tab'][data-value='{region_name.upper().replace(' ', '_')}']"
        )
        if not await click_and_verify(page, region_selector, f"{region_name} Tab"):
            # Fallback attempt with text if data-value fails
            print("data-value selector failed, trying with text...")
            region_selector_fallback = f"button[role='tab']:has-text('{region_name}')"
            if not await click_and_verify(
                page, region_selector_fallback, f"{region_name} Tab (fallback)"
            ):
                print(
                    f"Could not click on {region_name} tab. Aborting this verification."
                )
                return

        # 2. Locate the server container by its text
        print(f"Searching for location '{location_name}'...")
        location_tile = page.locator(
            "div.ods-card", has_text=re.compile(location_name, re.I)
        ).first
        await location_tile.wait_for(state="visible", timeout=5000)

        # 3. Check if it's disabled
        # The main container has the 'disabled' class if not available
        class_attr = await location_tile.get_attribute("class") or ""
        if "disabled" in class_attr:
            print(
                f"-> Location {location_code} ({region_name}) not available (container disabled)."
            )
            return

        # Double verification: the internal input also has the 'disabled' attribute
        location_input = location_tile.locator(f"input[name='{location_code}']")
        if await location_input.is_disabled():
            print(
                f"-> Location {location_code} ({region_name}) not available (input disabled)."
            )
            return

        # 4. If we get here, it's available. Notify.
        msg = f"✅ Server available in *{region_name}*!\n\n- Location: *{location_name} ({location_code})*\n- [Book now]({URL})"
        notify(msg)

    except PWTimeoutError:
        print(
            f"-> Timeout waiting for location {location_code} in {region_name}. Probably not visible or available."
        )
    except Exception as e:
        print(f"-> Unexpected error verifying {location_code} in {region_name}: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()
        try:
            print(f"Opening {URL}...")
            await page.goto(URL, wait_until="networkidle", timeout=TIMEOUT)
            await accept_cookies(page)
            await page.wait_for_timeout(3000)  # Wait longer for the page to stabilize

            # --- Base configuration selection ---
            print("--- Starting base configuration selection ---")

            # Select VPS-2 (using real HTML selector)
            vps2_selector = "label[for*='vps-2025-model2']"
            if not await click_and_verify(page, vps2_selector, "VPS-2 Option"):
                # Alternative selector
                vps2_selector_alt = "input[value='vps-2025-model2']"
                await page.locator(vps2_selector_alt).click()
                await page.wait_for_timeout(1000)

            # Select "No commitment"
            no_commitment_selector = "label[for*='default']"
            if not await click_and_verify(
                page, no_commitment_selector, "No commitment Option"
            ):
                # Alternative selector
                no_commitment_selector_alt = "input[value='default']"
                await page.locator(no_commitment_selector_alt).click()
                await page.wait_for_timeout(1000)

            print("\n--- Base configuration selected. Checking locations ---")

            # --- Availability checks ---
            # North America (Canada)
            await check_availability(
                page, "North America", "Canada - East - Beauharnois", "BHS"
            )

            # Europe (France)
            await check_availability(page, "Europe", "France - Gravelines", "GRA")

            print("\n--- Verification completed. ---")

        except PWTimeoutError:
            notify(
                f"❌ Error: Timeout loading OVH configuration page ({URL}). Script could not complete."
            )
        except Exception as e:
            notify(f"❌ Unexpected error in script: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
