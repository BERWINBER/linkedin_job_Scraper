import time
import json
import os
from datetime import datetime
from typing import Dict, Optional, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# --- CONFIGURATION ---
# Paste ANY LinkedIn job URL here (either a /view/ or a /search/ link)
JOB_URL_TO_SCRAPE = "https://www.linkedin.com/jobs/search/?currentJobId=4255281290&geoId=103644278&keywords=ML%20Engineer&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true" # <--- CHANGE THIS URL

CHROME_DEBUGGER_ADDRESS = "127.0.0.1:9222"
WAIT_TIMEOUT = 15  # Increased timeout
SCROLL_PAUSE_TIME = 2

# --- ENHANCED SELECTORS ---
# Multiple selector fallbacks for better reliability
VIEW_PAGE_SELECTORS = {
    "title": [
        ".top-card-layout__title",
        ".top-card-layout__title h1",
        "h1.top-card-layout__title",
        ".job-details-jobs-unified-top-card__job-title h1",
        ".job-details-jobs-unified-top-card__job-title"
    ],
    "company_name": [
        ".top-card-layout__second-subline a.topcard__org-name-link",
        ".topcard__org-name-link",
        ".top-card-layout__second-subline a",
        ".job-details-jobs-unified-top-card__company-name",
        ".job-details-jobs-unified-top-card__company-name a"
    ],
    "location": [
        ".top-card-layout__second-subline > div:first-child",
        ".topcard__flavor--bullet",
        ".job-details-jobs-unified-top-card__bullet"
    ],
    "description_container": [
        ".description__text",
        ".jobs-description-content__text",
        ".jobs-description__content",
        ".job-details-jobs-unified-top-card__job-description",
        ".jobs-box__html-content"
    ],
    "description_show_more_button": [
        ".description__footer-button",
        ".jobs-description__footer-button",
        ".jobs-description-content__footer button",
        "button[data-tracking-control-name='public_jobs_show-more-html-btn']"
    ],
    "criteria_list": [
        ".description__job-criteria-list li",
        ".job-details-jobs-unified-top-card__job-insight",
        ".jobs-unified-top-card__job-insight",
        ".job-details-jobs-unified-top-card__job-insight-view-model"
    ]
}

SEARCH_PAGE_SELECTORS = {
    "details_pane": [
        ".scaffold-layout__detail",
        ".jobs-search__job-details",
        ".job-details-jobs-unified-top-card"
    ],
    "title": [
        ".job-details-jobs-unified-top-card__job-title",
        ".job-details-jobs-unified-top-card__job-title h1",
        ".jobs-unified-top-card__job-title",
        ".jobs-unified-top-card__job-title h1"
    ],
    "company_name": [
        "div.job-details-jobs-unified-top-card__primary-description-container a",
        ".job-details-jobs-unified-top-card__company-name",
        ".job-details-jobs-unified-top-card__company-name a",
        ".jobs-unified-top-card__subtitle-primary-grouping a"
    ],
    "location": [
        "div.job-details-jobs-unified-top-card__primary-description-container > div:nth-child(2)",
        ".job-details-jobs-unified-top-card__bullet",
        ".jobs-unified-top-card__bullet"
    ],
    "description_container": [
        ".jobs-description-content__text",
        ".jobs-description__content",
        ".job-details-jobs-unified-top-card__job-description",
        ".jobs-box__html-content"
    ],
    "description_show_more_button": [
        ".jobs-description__footer-button",
        ".jobs-description-content__footer button",
        "button[data-tracking-control-name='public_jobs_show-more-html-btn']"
    ],
    "criteria_list": [
        ".job-details-jobs-unified-top-card__job-insight",
        ".jobs-unified-top-card__job-insight",
        ".job-details-jobs-unified-top-card__job-insight-view-model"
    ]
}

class LinkedInJobScraper:
    """
    Enhanced LinkedIn job scraper with better content extraction and fallback mechanisms.
    """
    def __init__(self, job_url: str):
        self.job_url = job_url
        self.driver = self._initialize_driver()
        self.wait = WebDriverWait(self.driver, WAIT_TIMEOUT)
        self.page_type = self._detect_page_type()
        self.selectors = SEARCH_PAGE_SELECTORS if self.page_type == 'search' else VIEW_PAGE_SELECTORS

    def _initialize_driver(self) -> webdriver.Chrome:
        print("🔌 Connecting to existing Chrome session...")
        options = Options()
        options.debugger_address = CHROME_DEBUGGER_ADDRESS
        try:
            driver = webdriver.Chrome(options=options)
            print("✅ Successfully connected to Chrome.")
            return driver
        except Exception as e:
            print(f"❌ Error connecting to Chrome: {e}")
            raise

    def _detect_page_type(self) -> str:
        """Detects if the URL is for a search page or a direct view page."""
        if "/jobs/search/" in self.job_url:
            print("ℹ️ Search page URL detected. Using search-pane selectors.")
            return 'search'
        elif "/jobs/view/" in self.job_url:
            print("ℹ️ Direct view page URL detected. Using view-page selectors.")
            return 'view'
        else:
            print("⚠️ URL type not clearly detected. Defaulting to search page selectors.")
            return 'search'

    def _get_element_text_with_fallbacks(self, selector_key: str) -> Optional[str]:
        """Tries multiple selectors until one works."""
        selectors = self.selectors.get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                text = element.text.strip()
                if text:  # Only return non-empty text
                    print(f"✅ Found {selector_key} using selector: {selector}")
                    return text
            except TimeoutException:
                continue
            except Exception as e:
                print(f"⚠️ Error with selector {selector}: {e}")
                continue
        
        print(f"❌ Could not find {selector_key} with any selector")
        return None

    def _get_element_html_with_fallbacks(self, selector_key: str) -> Optional[str]:
        """Gets HTML content with fallback selectors."""
        selectors = self.selectors.get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                html = element.get_attribute('innerHTML')
                if html and html.strip():
                    print(f"✅ Found {selector_key} HTML using selector: {selector}")
                    return html.strip()
            except TimeoutException:
                continue
            except Exception as e:
                print(f"⚠️ Error with selector {selector}: {e}")
                continue
        
        print(f"❌ Could not find {selector_key} HTML with any selector")
        return None

    def _get_multiple_elements_text(self, selector_key: str) -> List[str]:
        """Gets text from multiple elements with fallback selectors."""
        selectors = self.selectors.get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    texts = [elem.text.strip() for elem in elements if elem.text.strip()]
                    if texts:
                        print(f"✅ Found {len(texts)} {selector_key} items using selector: {selector}")
                        return texts
            except Exception as e:
                print(f"⚠️ Error with selector {selector}: {e}")
                continue
        
        print(f"❌ Could not find {selector_key} with any selector")
        return []

    def _expand_description(self):
        """Clicks the 'see more' button if it exists."""
        selectors = self.selectors.get("description_show_more_button", [])
        if isinstance(selectors, str):
            selectors = [selectors]
        
        for selector in selectors:
            try:
                show_more_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                # Scroll to button first
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
                time.sleep(1)
                
                # Try clicking with JavaScript
                self.driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)
                print("✅ Expanded job description.")
                return
            except NoSuchElementException:
                continue
            except Exception as e:
                print(f"⚠️ Error clicking show more button: {e}")
                continue
        
        print("ℹ️ 'See more' button not found (description may be fully visible).")

    def _scroll_and_wait(self):
        """Scrolls the page to load dynamic content."""
        print("📜 Scrolling to load dynamic content...")
        
        # Scroll to bottom
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(SCROLL_PAUSE_TIME)

    def _extract_additional_info(self) -> Dict[str, any]:
        """Extracts additional job information that might be available."""
        additional_info = {}
        
        # Try to find job posting date
        date_selectors = [
            ".job-details-jobs-unified-top-card__primary-description-container time",
            ".jobs-unified-top-card__posted-date",
            ".job-details-jobs-unified-top-card__posted-date"
        ]
        
        for selector in date_selectors:
            try:
                date_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                additional_info["posted_date"] = date_element.text.strip()
                break
            except:
                continue
        
        # Try to find job type (Full-time, Part-time, etc.)
        job_type_selectors = [
            ".job-details-jobs-unified-top-card__job-insight span",
            ".jobs-unified-top-card__job-insight span"
        ]
        
        for selector in job_type_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if any(keyword in text.lower() for keyword in ['full-time', 'part-time', 'contract', 'internship']):
                        additional_info["job_type"] = text
                        break
                if "job_type" in additional_info:
                    break
            except:
                continue
        
        # Try to find seniority level
        seniority_keywords = ['entry level', 'associate', 'mid-senior', 'director', 'executive']
        for selector in job_type_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip().lower()
                    for keyword in seniority_keywords:
                        if keyword in text:
                            additional_info["seniority_level"] = elem.text.strip()
                            break
                if "seniority_level" in additional_info:
                    break
            except:
                continue
        
        return additional_info

    def run(self) -> Optional[Dict[str, any]]:
        """Main orchestration method."""
        print(f"🚀 Navigating to job page: {self.job_url}")
        self.driver.get(self.job_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # For search pages, we need to wait for the details pane to load
        if self.page_type == 'search':
            details_pane_selectors = self.selectors.get("details_pane", [])
            if isinstance(details_pane_selectors, str):
                details_pane_selectors = [details_pane_selectors]
            
            pane_loaded = False
            for selector in details_pane_selectors:
                try:
                    self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                    print("✅ Job details pane is visible.")
                    pane_loaded = True
                    break
                except TimeoutException:
                    continue
            
            if not pane_loaded:
                print("❌ Timed out waiting for job details pane to load. Trying to continue anyway...")

        # Scroll to load dynamic content
        self._scroll_and_wait()

        # Expand description
        self._expand_description()

        print("🔍 Extracting job details...")

        # Extract basic information
        title = self._get_element_text_with_fallbacks("title")
        if not title:
            print("❌ Critical failure: Could not extract job title. Aborting.")
            return None

        company_name = self._get_element_text_with_fallbacks("company_name")
        location = self._get_element_text_with_fallbacks("location")
        
        # Extract description HTML
        description_html = self._get_element_html_with_fallbacks("description_container")
        
        # Extract description text as fallback
        description_text = self._get_element_text_with_fallbacks("description_container")
        
        # Extract criteria/insights
        criteria = self._get_multiple_elements_text("criteria_list")
        
        # Extract additional information
        additional_info = self._extract_additional_info()
        
        # Find salary information
        salary_info = None
        for criterion in criteria:
            if any(s in criterion.lower() for s in ['$', '€', '£', '₹', 'salary', 'compensation', 'pay']):
                salary_info = criterion
                break
        
        if salary_info:
            print(f"💰 Found potential salary information: {salary_info}")

        job_data = {
            "job_title": title,
            "company_name": company_name,
            "location": location,
            "salary_info": salary_info,
            "job_criteria": criteria,
            "job_description_html": description_html,
            "job_description_text": description_text,
            "url": self.job_url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **additional_info  # Add any additional extracted info
        }
        
        print("✅ Extraction complete.")
        return job_data

def save_data_to_json(data: Dict):
    """Saves the extracted data to a JSON file."""
    if not data or not data.get("job_title"):
        print("❌ No valid data to save.")
        return
        
    safe_title = "".join(c for c in data["job_title"] if c.isalnum() or c in " -_").rstrip()
    filename = f"job_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Data successfully saved to: {filename}")
    except IOError as e:
        print(f"❌ Error saving data to file: {e}")

def print_extracted_data(data: Dict):
    """Pretty prints the extracted data."""
    if not data:
        return
    
    print("\n" + "="*60)
    print("📄 SCRAPED JOB DETAILS")
    print("="*60)
    
    # Print main details
    print(f"🏢 Title: {data.get('job_title', 'N/A')}")
    print(f"🏬 Company: {data.get('company_name', 'N/A')}")
    print(f"📍 Location: {data.get('location', 'N/A')}")
    print(f"💰 Salary: {data.get('salary_info', 'N/A')}")
    
    if data.get('job_type'):
        print(f"⏰ Job Type: {data.get('job_type')}")
    
    if data.get('seniority_level'):
        print(f"📈 Seniority: {data.get('seniority_level')}")
    
    if data.get('posted_date'):
        print(f"📅 Posted: {data.get('posted_date')}")
    
    if data.get('job_criteria'):
        print(f"📋 Criteria: {', '.join(data.get('job_criteria', []))}")
    
    print(f"🔗 URL: {data.get('url', 'N/A')}")
    print(f"🕐 Scraped: {data.get('scraped_at', 'N/A')}")
    
    # Print description preview
    if data.get('job_description_text'):
        desc_preview = data['job_description_text'][:200] + "..." if len(data['job_description_text']) > 200 else data['job_description_text']
        print(f"\n📝 Description Preview:\n{desc_preview}")
    
    print("="*60)

if __name__ == "__main__":
    if "CHANGE THIS URL" in JOB_URL_TO_SCRAPE or not JOB_URL_TO_SCRAPE:
        print("🔴 ERROR: Please update the 'JOB_URL_TO_SCRAPE' variable before running.")
    else:
        try:
            scraper = LinkedInJobScraper(job_url=JOB_URL_TO_SCRAPE)
            job_details = scraper.run()

            if job_details:
                print_extracted_data(job_details)
                save_data_to_json(job_details)
                
                # Additional debug info
                print(f"\n🔍 DEBUG INFO:")
                print(f"- Found {len(job_details.get('job_criteria', []))} criteria items")
                print(f"- Description HTML length: {len(job_details.get('job_description_html', ''))}")
                print(f"- Description text length: {len(job_details.get('job_description_text', ''))}")
                
            else:
                print("\n❌ Could not scrape any details from the provided URL.")
                print("🔧 Troubleshooting tips:")
                print("- Make sure you're logged into LinkedIn in the Chrome browser")
                print("- Check if the URL is accessible and loads properly")
                print("- LinkedIn may have updated their HTML structure")
                
        except Exception as e:
            print(f"\n💥 A fatal error occurred: {e}")
            import traceback
            traceback.print_exc()
