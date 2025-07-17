from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def automate_linkedin_job_search(job_title="ML Engineer", location="Bengaluru, Karnataka, India", experience_levels=None, wait_time=10):
    """
    Automate LinkedIn job search using an existing Chrome session.
    Searches, filters by location, and then filters by experience level.

    Args:
        job_title (str): The job title to search for.
        location (str): Location filter.
        experience_levels (list): A list of experience levels to filter by (e.g., ["Entry level", "Associate"]).
        wait_time (int): Time to wait at the end before finishing.

    Returns:
        bool: True if automation completed successfully, False otherwise.
    """
    if experience_levels is None:
        experience_levels = []

    # Connect to Chrome already opened in debugging mode
    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20) # Increased wait time for stability

        print(f"🔍 Starting LinkedIn job search for '{job_title}'...")

        # Step 1: Go to LinkedIn
        driver.get("https://www.linkedin.com")
        time.sleep(3)

        # Step 2: Find and use the main search bar
        try:
            search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-global-typeahead__input")))
            search_box.clear()
            search_box.send_keys(job_title)
            search_box.send_keys(Keys.RETURN)
            print(f"✅ Searched for: {job_title}")
            time.sleep(5)
        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to find main search bar: {e}")
            return False

        # Step 3: Click the "Jobs" tab in the filter row
        try:
            jobs_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Jobs']")))
            jobs_tab.click()
            print("✅ Successfully filtered to Jobs tab.")
            time.sleep(5)
        except (TimeoutException, NoSuchElementException) as e:
            print(f"❌ Failed to click Jobs tab: {e}")
            return False

        # ✨ NEW: Step 4 - Filter by Experience Level ✨
        if experience_levels:
            print(f"💼 Applying Experience Level filter for: {', '.join(experience_levels)}")
            try:
                # 1. Click the main "Experience level" button to reveal the dropdown.
                exp_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Experience level']")))
                exp_button.click()
                print("✅ Opened 'Experience level' dropdown.")
                time.sleep(2)

                # 2. Loop through each desired level and tick its checkbox.
                for level in experience_levels:
                    try:
                        # Find the label for the checkbox (e.g., "Entry level") and click it to tick the box.
                        level_label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[normalize-space()='{level}']")))
                        driver.execute_script("arguments[0].click();", level_label) # More reliable click
                        print(f"  ✔️  Ticked checkbox for: {level}")
                        time.sleep(0.5)
                    except (TimeoutException, NoSuchElementException):
                        print(f"  ⚠️  Could not find checkbox for '{level}'. Skipping.")

                # 3. After ticking all boxes, click the "Show results" button to apply the filters.
                # Try multiple selectors for the "Show results" button
                show_results_clicked = False
                
                # Selector 1: Try the original XPath
                try:
                    show_results_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Show results']]")))
                    show_results_button.click()
                    show_results_clicked = True
                    print("✅ Clicked 'Show results' to apply experience filter (Method 1).")
                except (TimeoutException, NoSuchElementException):
                    print("⚠️  Method 1 failed, trying alternative selectors...")

                # Selector 2: Try direct text match
                if not show_results_clicked:
                    try:
                        show_results_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Show results']")))
                        show_results_button.click()
                        show_results_clicked = True
                        print("✅ Clicked 'Show results' to apply experience filter (Method 2).")
                    except (TimeoutException, NoSuchElementException):
                        print("⚠️  Method 2 failed, trying Method 3...")

                # Selector 3: Try contains text
                if not show_results_clicked:
                    try:
                        show_results_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show results')]")))
                        show_results_button.click()
                        show_results_clicked = True
                        print("✅ Clicked 'Show results' to apply experience filter (Method 3).")
                    except (TimeoutException, NoSuchElementException):
                        print("⚠️  Method 3 failed, trying Method 4...")

                # Selector 4: Try CSS selector approach
                if not show_results_clicked:
                    try:
                        show_results_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_f_L']")))
                        show_results_button.click()
                        show_results_clicked = True
                        print("✅ Clicked 'Show results' to apply experience filter (Method 4).")
                    except (TimeoutException, NoSuchElementException):
                        print("⚠️  Method 4 failed, trying Method 5...")

                # Selector 5: Try finding by aria-label or other attributes
                if not show_results_clicked:
                    try:
                        # Look for button with specific classes that might indicate it's the show results button
                        show_results_button = driver.find_element(By.XPATH, "//button[contains(@class, 'artdeco-button') and contains(@class, 'artdeco-button--primary')]")
                        button_text = show_results_button.text.strip().lower()
                        if 'show' in button_text and 'result' in button_text:
                            show_results_button.click()
                            show_results_clicked = True
                            print("✅ Clicked 'Show results' to apply experience filter (Method 5).")
                    except (TimeoutException, NoSuchElementException):
                        print("⚠️  Method 5 failed, trying Method 6...")

                # Selector 6: Last resort - try to find any primary button in the modal
                if not show_results_clicked:
                    try:
                        # Find all buttons and look for one with "Show results" text
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if button.text.strip().lower() == 'show results':
                                driver.execute_script("arguments[0].click();", button)
                                show_results_clicked = True
                                print("✅ Clicked 'Show results' to apply experience filter (Method 6).")
                                break
                    except Exception as e:
                        print(f"⚠️  Method 6 failed: {e}")

                if not show_results_clicked:
                    print("❌ All methods failed to click 'Show results' button.")
                    print("🔍 Let's try to debug - printing all visible buttons:")
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for i, button in enumerate(buttons):
                            if button.is_displayed():
                                print(f"  Button {i}: '{button.text.strip()}' - Classes: {button.get_attribute('class')}")
                    except:
                        pass
                    
                    # Press Escape to close the modal
                    print("🔄 Pressing Escape to close the modal...")
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    return False

                time.sleep(5)

            except (TimeoutException, NoSuchElementException) as e:
                print(f"❌ An error occurred while applying the experience filter: {e}")
                # Press Escape to close the pop-up if something went wrong
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
                return False

        print(f"✅ Automation completed!")
        print(f"🕐 Waiting {wait_time} seconds before finishing...")
        time.sleep(wait_time)

        return True

    except Exception as e:
        print(f"❌ An unexpected error occurred during automation: {e}")
        return False

    finally:
        print("🔄 Browser session maintained for further use.")

def main():
    """Main function to run the job search automation."""
    # --- Configuration ---
    JOB_TITLE = "ML Engineer"
    LOCATION = "Bengaluru, Karnataka, India" # Note: Location filter is now part of the initial search
    
    # --- ✨ Specify the experience levels you want to select ---
    # The text must EXACTLY match what's on LinkedIn.
    EXPERIENCE_LEVELS = ["Entry level", "Associate"]
    
    WAIT_TIME = 20

    print("🚀 Starting LinkedIn Job Search Automation...")
    print(f"Search Parameters: '{JOB_TITLE}' in '{LOCATION}'")
    if EXPERIENCE_LEVELS:
        print(f"Experience Levels: {', '.join(EXPERIENCE_LEVELS)}")
    print("=" * 60)

    # Note: The location is not passed as a separate argument anymore,
    # as the new flow doesn't use the secondary location filter.
    success = automate_linkedin_job_search(JOB_TITLE, LOCATION, EXPERIENCE_LEVELS, WAIT_TIME)

    if success:
        print("\n✅ Automation completed successfully!")
        print("You can now manually browse the job results.")
    else:
        print("\n❌ Automation failed. Please check the error messages above.")

    print("\n🎉 Process finished.")

if __name__ == "__main__":
    main()
