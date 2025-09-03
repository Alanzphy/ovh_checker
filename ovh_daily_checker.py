"""
OVH VPS Availability Checker

This script automatically checks for VPS-2 server availability on OVH's configu    try:
        print(f"Attempting to click '{name}' with selector '{selector}'...")

        # Wait longer for page to stabilize before looking for element
        await page.wait_for_timeout(1000)  # Reduced from 3000ms

        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=20000)  # Keep long timeout for visibility

        # Additional wait to ensure element is fully loaded and clickable
        await page.wait_for_timeout(1000)  # Reduced from 2000ms
        print(f"Element '{name}' is visible, attempting click...")e
and sends Telegram notifications when servers become available.

Regions monitored:
- North America: Canada - East - Beauharnois (BHS)
- Europe: France - Gravelines (GRA)
License: MIT
"""

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
TIMEOUT = 60000
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
        print("Waiting for page to load completely...")
        await page.wait_for_timeout(3000)  # Wait 3 seconds for page to stabilize

        # Try multiple selectors for the cookie accept button
        cookie_selectors = [
            '#header_tc_privacy_button_3',  # Specific ID from HTML - most reliable
            'button[data-tc-privacy="cookie-banner::accept"]',  # OVH specific selector
            'button[title="Accept"]',  # Title attribute
            'button[data-navi-id="cookie-accept"]',  # OVH navigation ID
            'button:has-text("Accept")',  # Text content
        ]

        # First check if overlay exists
        overlay_exists = await page.locator("#tc_priv_CustomOverlay").count() > 0
        if overlay_exists:
            print("🍪 Cookie overlay detected! Attempting to click Accept...")

        cookie_found = False
        for selector in cookie_selectors:
            try:
                print(f"  Trying cookie selector: {selector}")
                cookie_btn = page.locator(selector).first

                if await cookie_btn.count() > 0:
                    print(f"  ✅ Found cookie button! Clicking...")
                    await cookie_btn.wait_for(state="visible", timeout=5000)
                    await cookie_btn.click(timeout=10000)
                    print("  ✅ Cookie button clicked!")

                    # Wait for overlay to disappear
                    if overlay_exists:
                        try:
                            await page.wait_for_selector("#tc_priv_CustomOverlay", state="detached", timeout=10000)
                            print("  🎉 Cookie overlay removed successfully!")
                        except:
                            print("  ⚠️ Overlay still present, forcing removal...")
                            await page.evaluate("""
                                const overlay = document.querySelector('#tc_priv_CustomOverlay');
                                if (overlay) overlay.remove();
                                const banner = document.querySelector('#header_tc_privacy');
                                if (banner) banner.remove();
                            """)

                    await page.wait_for_timeout(1000)  # Shorter wait after click
                    cookie_found = True
                    break
            except Exception as e:
                print(f"  Cookie selector {selector} failed: {e}")
                continue

        if not cookie_found and overlay_exists:
            print("❌ No cookie button worked, forcing overlay removal...")
            await page.evaluate("""
                const overlay = document.querySelector('#tc_priv_CustomOverlay');
                if (overlay) overlay.remove();
                const banner = document.querySelector('#header_tc_privacy');
                if (banner) banner.remove();
            """)
            await page.wait_for_timeout(1000)  # Shorter wait after forced removal

    except Exception as e:
        print(f"Cookie handling error: {e}")
        pass
async def click_and_verify(page, selector, name, force=False):
    """Locates, clicks an element and verifies it becomes selected."""
    try:
        print(f"Attempting to click '{name}' with selector '{selector}'...")

        await page.wait_for_timeout(3000)

        element = page.locator(selector).first
        await element.wait_for(state="visible", timeout=20000)

        await page.wait_for_timeout(2000)
        print(f"Element '{name}' is visible, attempting click...")

        if force:
            await element.click(force=True, timeout=10000)
        else:
            await element.click(timeout=10000)

        print(f"✅ Successful click on '{name}'.")

        # For radio buttons, verify the input is checked
        try:
            # If it's a label, find the associated input
            if selector.startswith("label"):
                for_attr = await element.get_attribute("for")
                if for_attr:
                    input_element = page.locator(f"input[id='{for_attr}']")
                    # Wait a bit for the state to change
                    await page.wait_for_timeout(500)  # Reduced from 1000ms
                    is_checked = await input_element.is_checked()
                    if is_checked:
                        print(f"✅ '{name}' confirmed as selected (radio checked).")
                    else:
                        print(f"⚠️ '{name}' - clicked but radio not checked yet.")
                else:
                    print(f"⚠️ '{name}' - label has no 'for' attribute.")
            # If it's an input, check if it's checked
            elif selector.startswith("input"):
                await page.wait_for_timeout(500)  # Reduced from 1000ms
                is_checked = await element.is_checked()
                if is_checked:
                    print(f"✅ '{name}' confirmed as selected (input checked).")
                else:
                    print(f"⚠️ '{name}' - clicked but not checked yet.")
            else:
                print(f"✅ '{name}' - clicked successfully.")
        except Exception as verify_error:
            print(f"⚠️ '{name}' - click performed but verification failed: {verify_error}")

        await page.wait_for_timeout(1000)  # Shorter pause for UI to update (reduced from 5s)
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
        await page.wait_for_timeout(1000)  # Wait for tab content to load (reduced from 3000ms)

        location_tile = page.locator(
            "div.ods-card", has_text=re.compile(location_name, re.I)
        ).first
        await location_tile.wait_for(state="visible", timeout=15000)

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

            # Handle cookies popup
            await accept_cookies(page)

            print("Checking if cookie popup is closed...")
            try:
                cookie_overlay = page.locator("#tc_priv_CustomOverlay")
                if await cookie_overlay.count() > 0:
                    await cookie_overlay.wait_for(state="hidden", timeout=10000)
                    print("Cookie overlay confirmed as closed")
            except:
                print("Cookie overlay check completed")

            await page.wait_for_timeout(3000)

            print("--- Starting base configuration selection ---")

            print("Waiting for page elements to be fully loaded...")
            await page.wait_for_timeout(2000)

            # Handle any additional popups that might interfere with clicks
            print("🚫 Checking for interfering popups...")
            try:
                # Check for geolocation popup
                geo_popup = page.locator("#geoPopin")
                if await geo_popup.count() > 0:
                    print("  Found geo popup, attempting to close...")
                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(1000)
                    except:
                        pass

                    # Force remove if still there
                    try:
                        await page.evaluate("""
                            const geoPopup = document.querySelector('#geoPopin');
                            if (geoPopup) {
                                geoPopup.remove();
                                console.log('Geo popup removed');
                            }
                        """)
                    except:
                        pass

                # Check for any other modal dialogs
                modals = await page.locator("dialog[open], .modal[style*='block']").all()
                if modals:
                    print(f"  Found {len(modals)} modal dialogs, trying to close...")
                    for modal in modals:
                        try:
                            await modal.evaluate("el => el.remove()")
                        except:
                            pass

                print("  ✅ Popup cleanup completed")
                await page.wait_for_timeout(2000)

            except Exception as e:
                print(f"  Popup handling error: {e}")
            # Select VPS-2
            print("Attempting to select VPS-2 option...")

            vps2_selectors = [
                "input[id='radio-group:«r0»:radio:input:vps-2025-model2']",  # Direct input
                "label[for='radio-group:«r0»:radio:input:vps-2025-model2']",  # Label
                "input[value='vps-2025-model2']",  # By value
                "label:has-text('VPS-2')",  # By text content
            ]

            vps2_selected = False
            for selector in vps2_selectors:
                try:
                    print(f"  Trying VPS-2 selector: {selector}")
                    if await click_and_verify(page, selector, f"VPS-2 Option ({selector})"):
                        vps2_selected = True
                        break
                except Exception as e:
                    print(f"  Selector failed: {e}")
                    continue

            if not vps2_selected:
                print("❌ All VPS-2 selectors failed, trying force methods...")
                try:
                    # Force approach 1: Scroll to element and force click
                    vps2_input = page.locator("input[value='vps-2025-model2']")
                    await vps2_input.scroll_into_view_if_needed()
                    await page.wait_for_timeout(1000)
                    await vps2_input.click(force=True, timeout=10000)
                    await page.wait_for_timeout(1000)  # Reduced from 3000ms
                    print("✅ VPS-2 clicked with force")
                    vps2_selected = True
                except Exception as e:
                    print(f"❌ Force click failed: {e}")

                    # Force approach 2: JavaScript click
                    try:
                        print("Trying JavaScript click...")
                        await page.evaluate("""
                            const input = document.querySelector('input[value="vps-2025-model2"]');
                            if (input) {
                                input.click();
                                input.checked = true;
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """)
                        await page.wait_for_timeout(1000)  # Reduced from 3000ms
                        print("✅ VPS-2 clicked via JavaScript")
                        vps2_selected = True
                    except Exception as e2:
                        print(f"❌ JavaScript click also failed: {e2}")

            # Select "No commitment"
            print("Attempting to select No commitment option...")
            no_commitment_selector = "label[for*='default']"
            if not await click_and_verify(
                page, no_commitment_selector, "No commitment Option"
            ):
                print("Primary selector failed, trying alternative selector...")
                # Alternative selector
                no_commitment_selector_alt = "input[value='default']"
                await page.locator(no_commitment_selector_alt).click(timeout=10000)
                await page.wait_for_timeout(1000)  # Reduced from 3000ms

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
