from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime
from collections import Counter
import os

def search_linkedin_jobs(job_title="Data Analyst", location="", wait_time=10):
    """
    Search for jobs on LinkedIn using an existing Chrome session in debugging mode.
    
    Args:
        job_title (str): The job title to search for
        location (str): Location filter (optional)
        wait_time (int): Time to wait at the end before closing
    
    Returns:
        list: List of job dictionaries with details
    """
    
    # Connect to Chrome already opened in debugging mode
    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        print(f"🔍 Searching for '{job_title}' jobs on LinkedIn...")
        
        # Step 1: Go to LinkedIn
        driver.get("https://www.linkedin.com")
        time.sleep(3)
        
        # Step 2: Find and use the search bar
        try:
            # Try multiple possible selectors for the search box
            search_selectors = [
                "input[placeholder='Search']",
                "input[aria-label='Search']",
                ".search-global-typeahead__input",
                "input[type='text'][placeholder*='Search']"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if not search_box:
                print("❌ Could not find search box")
                return []
            
            # Clear and enter search term
            search_box.clear()
            search_box.send_keys(job_title)
            search_box.send_keys(Keys.RETURN)
            print(f"✅ Searched for: {job_title}")
            
            # Wait for results to load
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Failed to perform search: {e}")
            return []
        
        # Step 3: Click the Jobs tab in the filter row
        try:
            # Target the specific Jobs button in the filter tabs
            jobs_selectors = [
                "//button[text()='Jobs']",  # Direct text match
                "//button[contains(@class, 'search-reusables__filter-pill-button') and contains(text(), 'Jobs')]",
                "//div[contains(@class, 'search-reusables__primary-filter')]//button[text()='Jobs']",
                ".search-reusables__primary-filter button[aria-pressed='false']:has-text('Jobs')",
                "button[data-test-reusables-search-filter-pill='Jobs']"
            ]
            
            jobs_tab = None
            for selector in jobs_selectors:
                try:
                    if selector.startswith("//"):
                        jobs_tab = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:
                        jobs_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if jobs_tab:
                jobs_tab.click()
                print("✅ Successfully filtered to Jobs tab")
                time.sleep(3)
                
                # Optional: Add location filter
                if location:
                    try:
                        location_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label*='City']")
                        location_input.clear()
                        location_input.send_keys(location)
                        location_input.send_keys(Keys.RETURN)
                        print(f"✅ Added location filter: {location}")
                        time.sleep(3)
                    except:
                        print("⚠️ Could not add location filter")
                
                # Get job count
                try:
                    results_count = driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list__text")
                    print(f"📊 {results_count.text}")
                except:
                    print("📊 Jobs loaded successfully")
                    
            else:
                print("❌ Could not find Jobs tab")
                
        except Exception as e:
            print(f"❌ Failed to click Jobs tab: {e}")
        
        # Step 4: Scroll to load more results
        print("📜 Scrolling to load more results...")
        for i in range(5):  # Increased scrolling for more jobs
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # Step 5: Extract job listings
        print("🔍 Extracting job listings...")
        jobs = extract_job_listings(driver, max_jobs=50, debug_mode=False)
        
        print(f"\n✅ Job search and extraction completed! Found {len(jobs)} jobs. Keeping browser open for {wait_time} seconds...")
        time.sleep(wait_time)
        
        return jobs
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return []
    
    finally:
        # Note: Not closing driver to keep session active
        print("🔄 Browser session maintained for further use")

def debug_job_card_structure(driver, card_index=0):
    """
    Debug function to analyze the structure of job cards.
    
    Args:
        driver: Selenium WebDriver instance
        card_index (int): Index of the job card to analyze (0-based)
    """
    try:
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
        if not job_cards:
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".job-card-container")
        
        if job_cards and card_index < len(job_cards):
            card = job_cards[card_index]
            print(f"\n🔍 DEBUG: Analyzing job card {card_index + 1}")
            print("=" * 50)
            
            # Get all text elements
            all_elements = card.find_elements(By.CSS_SELECTOR, "*")
            for i, elem in enumerate(all_elements[:20]):  # Limit to first 20 elements
                try:
                    text = elem.text.strip()
                    tag = elem.tag_name
                    classes = elem.get_attribute("class")
                    if text and len(text) < 100:  # Skip very long text
                        print(f"{i+1}. <{tag}> class='{classes}' text='{text}'")
                except:
                    continue
            
            print("=" * 50)
            
            # Try to find company-related elements
            company_candidates = card.find_elements(By.CSS_SELECTOR, "h4, [class*='company'], [class*='subtitle'], a")
            print("\n🏢 Company candidates:")
            for i, elem in enumerate(company_candidates[:10]):
                try:
                    text = elem.text.strip()
                    classes = elem.get_attribute("class")
                    if text:
                        print(f"{i+1}. class='{classes}' text='{text}'")
                except:
                    continue
                    
        else:
            print(f"❌ No job card found at index {card_index}")
            
    except Exception as e:
        print(f"❌ Debug error: {e}")

def extract_job_listings(driver, max_jobs=50, debug_mode=False):
    """
    Extract job listings from the current LinkedIn jobs page.
    
    Args:
        driver: Selenium WebDriver instance
        max_jobs (int): Maximum number of jobs to extract
        debug_mode (bool): Enable debug output for troubleshooting
    
    Returns:
        list: List of job dictionaries with details
    """
    jobs = []
    
    try:
        # Debug mode - analyze first job card structure
        if debug_mode:
            debug_job_card_structure(driver, 0)
        
        # Wait for job cards to load
        wait = WebDriverWait(driver, 10)
        
        # Multiple selectors for job cards (LinkedIn changes these frequently)
        job_card_selectors = [
            ".jobs-search-results__list-item",
            ".job-card-container",
            ".jobs-search-results-list__item",
            "[data-job-id]",
            ".job-card-list"
        ]
        
        job_cards = []
        for selector in job_card_selectors:
            try:
                job_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                if job_cards:
                    print(f"✅ Found {len(job_cards)} job cards using selector: {selector}")
                    break
            except TimeoutException:
                continue
        
        if not job_cards:
            print("❌ No job cards found with any selector")
            return []
        
        print(f"🔍 Processing {min(len(job_cards), max_jobs)} job listings...")
        
        for i, card in enumerate(job_cards[:max_jobs]):
            try:
                job_data = {}
                
                # Job title
                title_selectors = [
                    ".base-search-card__title",
                    ".job-card-list__title",
                    ".jobs-unified-top-card__job-title",
                    ".job-card-container__link",
                    "h3 a",
                    ".job-card-list__title-link",
                    ".job-card-list__title a"
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_element.text.strip()
                        title_text = ' '.join(title_text.split())
                        
                        if title_text:
                            job_data['title'] = title_text
                            
                            # Try to get job link
                            try:
                                if title_element.tag_name == 'a':
                                    job_data['job_link'] = title_element.get_attribute('href')
                                else:
                                    link_element = card.find_element(By.CSS_SELECTOR, f"{selector} a")
                                    job_data['job_link'] = link_element.get_attribute('href')
                            except:
                                try:
                                    link_element = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link, a[href*='/jobs/view/']")
                                    job_data['job_link'] = link_element.get_attribute('href')
                                except:
                                    pass
                            break
                    except:
                        continue
                
                if not job_data.get('title'):
                    job_data['title'] = "Title not found"
                
                # Company name
                company_selectors = [
                    ".artdeco-entity-lockup__subtitle",
                    ".base-search-card__subtitle",
                    ".job-card-container__company-name",
                    ".job-card-list__subtitle",
                    ".job-card-container__subtitle",
                    ".artdeco-entity-lockup__subtitle span",
                    "h4",
                    ".job-card-list__company-name"
                ]
                
                for selector in company_selectors:
                    try:
                        company_element = card.find_element(By.CSS_SELECTOR, selector)
                        company_text = company_element.text.strip()
                        company_text = ' '.join(company_text.split())
                        
                        if (company_text and 
                            len(company_text) > 0 and 
                            len(company_text) < 100 and
                            not any(word in company_text.lower() for word in 
                                   ['analyst', 'engineer', 'manager', 'developer', 'specialist', 'intern', 'associate'])):
                            job_data['company'] = company_text
                            break
                    except:
                        continue
                
                if not job_data.get('company'):
                    job_data['company'] = "Company not found"
                
                # Location
                location_selectors = [
                    ".job-search-card__location",
                    ".artdeco-entity-lockup__caption",
                    ".job-card-container__metadata-item",
                    ".jobs-unified-top-card__bullet",
                    ".job-card-container__metadata-wrapper",
                    ".job-card-list__metadata",
                    ".job-card-container__secondary-description"
                ]
                
                for selector in location_selectors:
                    try:
                        location_element = card.find_element(By.CSS_SELECTOR, selector)
                        location_text = location_element.text.strip()
                        location_text = ' '.join(location_text.split())
                        
                        if (location_text and 
                            not any(word in location_text.lower() for word in 
                                   ['ago', 'hour', 'day', 'week', 'month', 'year', 'posted', 'within'])):
                            job_data['location'] = location_text
                            break
                    except:
                        continue
                
                if not job_data.get('location'):
                    job_data['location'] = "Location not found"
                
                # Posted time
                time_selectors = [
                    ".job-card-container__metadata-item time",
                    ".jobs-unified-top-card__subtitle-secondary-grouping time",
                    ".job-card-list__metadata time",
                    "time"
                ]
                
                for selector in time_selectors:
                    try:
                        time_element = card.find_element(By.CSS_SELECTOR, selector)
                        job_data['posted_time'] = time_element.text.strip()
                        break
                    except:
                        continue
                
                # Job description snippet
                desc_selectors = [
                    ".job-card-list__footer-wrapper",
                    ".job-card-container__snippet",
                    ".job-card-list__snippet"
                ]
                
                for selector in desc_selectors:
                    try:
                        desc_element = card.find_element(By.CSS_SELECTOR, selector)
                        job_data['description'] = desc_element.text.strip()[:200] + "..."
                        break
                    except:
                        continue
                
                # Add extraction timestamp
                job_data['extracted_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                jobs.append(job_data)
                
                if (i + 1) % 10 == 0:
                    print(f"📊 Processed {i + 1} jobs...")
                
            except Exception as e:
                print(f"⚠️ Error extracting job {i+1}: {e}")
                continue
        
        print(f"✅ Successfully extracted {len(jobs)} job listings")
        return jobs
        
    except Exception as e:
        print(f"❌ Error extracting job listings: {e}")
        return []

def analyze_job_data(jobs):
    """
    Analyze job data to generate insights and statistics.
    
    Args:
        jobs (list): List of job dictionaries
    
    Returns:
        dict: Analysis results
    """
    if not jobs:
        return {}
    
    analysis = {
        'total_jobs': len(jobs),
        'extraction_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'companies': {},
        'locations': {},
        'posting_times': {},
        'title_keywords': {},
        'unique_companies': 0,
        'unique_locations': 0
    }
    
    # Count companies
    company_counter = Counter()
    for job in jobs:
        company = job.get('company', 'Unknown')
        if company != 'Company not found':
            company_counter[company] += 1
    
    analysis['companies'] = dict(company_counter.most_common(10))
    analysis['unique_companies'] = len(company_counter)
    
    # Count locations
    location_counter = Counter()
    for job in jobs:
        location = job.get('location', 'Unknown')
        if location != 'Location not found':
            location_counter[location] += 1
    
    analysis['locations'] = dict(location_counter.most_common(10))
    analysis['unique_locations'] = len(location_counter)
    
    # Count posting times
    time_counter = Counter()
    for job in jobs:
        posted_time = job.get('posted_time', 'Unknown')
        if posted_time:
            time_counter[posted_time] += 1
    
    analysis['posting_times'] = dict(time_counter.most_common(10))
    
    # Analyze job title keywords
    keyword_counter = Counter()
    for job in jobs:
        title = job.get('title', '').lower()
        if title and title != 'title not found':
            # Extract common keywords
            keywords = ['analyst', 'senior', 'junior', 'manager', 'engineer', 'developer', 'specialist', 'lead', 'principal', 'director']
            for keyword in keywords:
                if keyword in title:
                    keyword_counter[keyword] += 1
    
    analysis['title_keywords'] = dict(keyword_counter.most_common(10))
    
    return analysis

def generate_report(jobs, job_title="", location="", output_format="html"):
    """
    Generate a comprehensive report from job listings.
    
    Args:
        jobs (list): List of job dictionaries
        job_title (str): Search term used
        location (str): Location filter used
        output_format (str): Format for output ('html', 'txt', 'json')
    
    Returns:
        str: Generated report content
    """
    if not jobs:
        return "No jobs found to generate report."
    
    analysis = analyze_job_data(jobs)
    
    if output_format == "html":
        return generate_html_report(jobs, analysis, job_title, location)
    elif output_format == "json":
        return generate_json_report(jobs, analysis, job_title, location)
    else:
        return generate_text_report(jobs, analysis, job_title, location)

def generate_html_report(jobs, analysis, job_title, location):
    """Generate a modern, visually appealing HTML report."""

    # --- Helper logic for bar chart percentages ---
    def get_percentage(value, max_value):
        if not max_value or not value:
            return 0
        return round((value / max_value) * 100)

    # Find the max counts for scaling the bar charts
    max_company_count = max(analysis['companies'].values()) if analysis.get('companies') else 1
    max_location_count = max(analysis['locations'].values()) if analysis.get('locations') else 1
    max_keyword_count = max(analysis['title_keywords'].values()) if analysis.get('title_keywords') else 1

    # --- HTML & CSS Template ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LinkedIn Job Search Report: {job_title}</title>
        <style>
            :root {{
                --primary-color: #0A66C2; /* LinkedIn Blue */
                --secondary-color: #70B5F9;
                --bg-light: #f7f9fa;
                --card-bg: #ffffff;
                --text-dark: #212121;
                --text-light: #5f6368;
                --border-color: #e0e6eb;
                --shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                --shadow-hover: 0 6px 16px rgba(0, 0, 0, 0.12);
                --border-radius: 12px;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg-light);
                color: var(--text-dark);
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1200px;
                margin: auto;
            }}
            .header {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 40px 30px;
                border-radius: var(--border-radius);
                margin-bottom: 30px;
                text-align: center;
                box-shadow: var(--shadow);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 2.5em;
                font-weight: 700;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }}
            .header p {{
                margin: 0;
                font-size: 1.1em;
                opacity: 0.9;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .summary-card {{
                background: var(--card-bg);
                padding: 25px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }}
            .summary-card .value {{
                font-size: 2.8em;
                font-weight: 700;
                color: var(--primary-color);
                line-height: 1.1;
            }}
            .summary-card .label {{
                font-size: 1em;
                color: var(--text-light);
                font-weight: 500;
            }}
            .section-title {{
                font-size: 1.8em;
                font-weight: 600;
                color: var(--text-dark);
                margin-bottom: 20px;
                border-bottom: 3px solid var(--primary-color);
                padding-bottom: 10px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 25px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: var(--card-bg);
                padding: 25px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
            }}
            .stat-card h3 {{
                margin-top: 0;
                font-size: 1.4em;
                font-weight: 600;
                color: var(--primary-color);
            }}
            .stat-item {{
                display: grid;
                grid-template-columns: 1fr auto;
                align-items: center;
                margin-bottom: 15px;
                font-size: 0.95em;
            }}
            .stat-label {{ color: var(--text-dark); }}
            .stat-count {{ color: var(--text-light); font-weight: 500; }}
            .stat-bar-container {{
                grid-column: 1 / -1;
                background-color: #e9ecef;
                border-radius: 5px;
                height: 8px;
                margin-top: 5px;
                overflow: hidden;
            }}
            .stat-bar {{
                background-color: var(--secondary-color);
                height: 100%;
                border-radius: 5px;
                transition: width 0.5s ease-in-out;
            }}
            .job-listings {{
                background: var(--card-bg);
                padding: 30px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
            }}
            .job-card {{
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 25px;
                margin-bottom: 20px;
                background: #fff;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .job-card:hover {{
                transform: translateY(-5px);
                box-shadow: var(--shadow-hover);
                border-left: 5px solid var(--primary-color);
            }}
            .job-title {{
                font-size: 1.4em;
                font-weight: 600;
                color: var(--primary-color);
                margin: 0 0 10px;
            }}
            .job-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px 20px;
                color: var(--text-light);
                margin-bottom: 15px;
                font-size: 1em;
            }}
            .job-meta-item {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .job-description {{
                color: var(--text-light);
                font-size: 0.95em;
                margin-bottom: 20px;
            }}
            .job-link {{
                display: inline-block;
                background: var(--primary-color);
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                transition: background-color 0.2s ease;
            }}
            .job-link:hover {{
                background: #004182; /* Darker blue */
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                color: var(--text-light);
                font-size: 0.9em;
            }}
            @media (max-width: 992px) {{
                .stats-grid {{ grid-template-columns: 1fr; }}
            }}
            @media (max-width: 768px) {{
                body {{ padding: 15px; }}
                .header h1 {{ font-size: 2em; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>LinkedIn Job Report</h1>
                <p>Search Query: <strong>{job_title}</strong> {f"in <strong>{location}</strong>" if location else ""}</p>
                <p>Generated on: {analysis['extraction_date']}</p>
            </div>
            
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">{analysis['total_jobs']}</div>
                    <div class="label">Total Jobs Found</div>
                </div>
                <div class="summary-card">
                    <div class="value">{analysis['unique_companies']}</div>
                    <div class="label">Unique Companies</div>
                </div>
                <div class="summary-card">
                    <div class="value">{analysis['unique_locations']}</div>
                    <div class="label">Unique Locations</div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Top Hiring Companies</h3>
                    {''.join([f'''
                    <div class="stat-item">
                        <span class="stat-label">{company}</span>
                        <strong class="stat-count">{count} jobs</strong>
                        <div class="stat-bar-container">
                            <div class="stat-bar" style="width: {get_percentage(count, max_company_count)}%;"></div>
                        </div>
                    </div>''' for company, count in analysis['companies'].items()])}
                </div>
                
                <div class="stat-card">
                    <h3>Top Job Locations</h3>
                    {''.join([f'''
                    <div class="stat-item">
                        <span class="stat-label">{loc}</span>
                        <strong class="stat-count">{count} jobs</strong>
                        <div class="stat-bar-container">
                            <div class="stat-bar" style="width: {get_percentage(count, max_location_count)}%;"></div>
                        </div>
                    </div>''' for loc, count in analysis['locations'].items()])}
                </div>
                
                <div class="stat-card">
                    <h3>Common Keywords in Titles</h3>
                     {''.join([f'''
                    <div class="stat-item">
                        <span class="stat-label">{keyword.title()}</span>
                        <strong class="stat-count">{count} jobs</strong>
                        <div class="stat-bar-container">
                            <div class="stat-bar" style="width: {get_percentage(count, max_keyword_count)}%;"></div>
                        </div>
                    </div>''' for keyword, count in analysis['title_keywords'].items()])}
                </div>

                <div class="stat-card">
                    <h3>Posting Freshness</h3>
                    {''.join([f'''
                    <div class="stat-item">
                        <span class="stat-label">{time}</span>
                        <strong class="stat-count">{count} jobs</strong>
                    </div>''' for time, count in analysis['posting_times'].items()])}
                </div>
            </div>

            <div class="job-listings">
                <h2 class="section-title">Job Listings ({len(jobs)} total)</h2>
                {''.join([f'''
                <div class="job-card">
                    <h3 class="job-title">{job.get('title', 'N/A')}</h3>
                    <div class="job-meta">
                        <span class="job-meta-item">🏢 {job.get('company', 'N/A')}</span>
                        <span class="job-meta-item">📍 {job.get('location', 'N/A')}</span>
                        {f'<span class="job-meta-item">🕒 {job.get("posted_time", "N/A")}</span>' if job.get('posted_time') else ''}
                    </div>
                    {f'<p class="job-description">{job.get("description", "")}</p>' if job.get('description') else ''}
                    {f'<a href="{job.get("job_link", "#")}" class="job-link" target="_blank">View Job on LinkedIn ↗</a>' if job.get('job_link') else ''}
                </div>
                ''' for job in jobs])}
            </div>

            <div class="footer">
                <p>Report generated by LinkedIn Job Scraper | Data extracted on {analysis['extraction_date']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def generate_text_report(jobs, analysis, job_title, location):
    """Generate text report."""
    report = f"""
{'='*80}
                     LINKEDIN JOB SEARCH REPORT
{'='*80}

Search Query: "{job_title}" {f"in {location}" if location else ""}
Generated on: {analysis['extraction_date']}
Total Jobs Found: {analysis['total_jobs']}

{'='*80}
                        EXECUTIVE SUMMARY
{'='*80}

This report contains {analysis['total_jobs']} job listings extracted from LinkedIn.
The search revealed opportunities across {analysis['unique_companies']} unique companies 
and {analysis['unique_locations']} different locations.

{'='*80}
                         ANALYTICS
{'='*80}

🏢 TOP COMPANIES:
{'-'*40}
"""
    
    for company, count in analysis['companies'].items():
        report += f"{company:<30} {count:>5} jobs\n"
    
    report += f"\n📍 TOP LOCATIONS:\n{'-'*40}\n"
    for location, count in analysis['locations'].items():
        report += f"{location:<30} {count:>5} jobs\n"
    
    report += f"\n⏰ POSTING TIMES:\n{'-'*40}\n"
    for time, count in analysis['posting_times'].items():
        report += f"{time:<30} {count:>5} jobs\n"
    
    report += f"\n🔍 TITLE KEYWORDS:\n{'-'*40}\n"
    for keyword, count in analysis['title_keywords'].items():
        report += f"{keyword.title():<30} {count:>5} jobs\n"
    
    report += f"\n{'='*80}\n                      DETAILED JOB LISTINGS\n{'='*80}\n\n"
    
    for i, job in enumerate(jobs, 1):
        report += f"{i}. {job.get('title', 'N/A')}\n"
        report += f"   Company: {job.get('company', 'N/A')}\n"
        report += f"   Location: {job.get('location', 'N/A')}\n"
        if job.get('posted_time'):
            report += f"   Posted: {job.get('posted_time')}\n"
        if job.get('description'):
            report += f"   Description: {job.get('description')}\n"
        if job.get('job_link'):
            report += f"   Link: {job.get('job_link')}\n"
        report += f"   Extracted: {job.get('extracted_at', 'N/A')}\n"
        report += f"{'-'*80}\n\n"
    
    report += f"Report generated by LinkedIn Job Scraper | Data extracted on {analysis['extraction_date']}\n"
    return report

def generate_json_report(jobs, analysis, job_title, location):
    """Generate JSON report."""
    report_data = {
        "report_metadata": {
            "search_query": job_title,
            "location_filter": location,
            "generation_date": analysis['extraction_date'],
            "total_jobs": analysis['total_jobs'],
            "unique_companies": analysis['unique_companies'],
            "unique_locations": analysis['unique_locations']
        },
        "analytics": {
            "top_companies": analysis['companies'],
            "top_locations": analysis['locations'],
            "posting_times": analysis['posting_times'],
            "title_keywords": analysis['title_keywords']
        },
        "job_listings": jobs
    }
    
    return json.dumps(report_data, indent=2, ensure_ascii=False)

def save_report(report_content, job_title, location="", output_format="html"):
    """
    Save the report to a file.
    
    Args:
        report_content (str): Report content
        job_title (str): Job title searched
        location (str): Location filter
        output_format (str): Output format
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    location_suffix = f"_{location.replace(' ', '_')}" if location else ""
    filename = f"linkedin_jobs_report_{job_title.replace(' ', '_')}{location_suffix}_{timestamp}.{output_format}"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📄 Report saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving report: {e}")
        return None

def main():
    """Main function to run the job search and generate reports."""
    # Configuration
    JOB_TITLE = "ML Engineer"  # Default job title
    LOCATION = "New York"  # Optional: specify location like "New York"
    OUTPUT_FORMATS = ["html", "txt", "json"]  # Generate multiple formats
    WAIT_TIME = 5  # Time to keep browser open after extraction
    
    print("🚀 Starting LinkedIn Job Search and Report Generation...")
    print(f"Search Parameters: '{JOB_TITLE}' {f'in {LOCATION}' if LOCATION else ''}")
    print("=" * 60)
    
    # Step 1: Search and extract jobs
    jobs = search_linkedin_jobs(JOB_TITLE, LOCATION, WAIT_TIME)
    
    if not jobs:
        print("❌ No jobs found. Please check your search parameters and try again.")
        return
    
    print(f"\n✅ Successfully extracted {len(jobs)} job listings!")
    
    # Step 2: Generate reports in multiple formats
    print("\n📊 Generating reports...")
    generated_files = []
    
    for format_type in OUTPUT_FORMATS:
        try:
            print(f"📝 Generating {format_type.upper()} report...")
            report_content = generate_report(jobs, JOB_TITLE, LOCATION, format_type)
            
            if report_content:
                filename = save_report(report_content, JOB_TITLE, LOCATION, format_type)
                if filename:
                    generated_files.append(filename)
                    
        except Exception as e:
            print(f"❌ Error generating {format_type} report: {e}")
    
    # Step 3: Display summary
    print("\n" + "=" * 60)
    print("📋 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total Jobs Found: {len(jobs)}")
    print(f"Reports Generated: {len(generated_files)}")
    
    if generated_files:
        print("\n📄 Generated Files:")
        for file in generated_files:
            print(f"  • {file}")
    
    # Step 4: Quick analytics preview
    analysis = analyze_job_data(jobs)
    print(f"\n📊 QUICK ANALYTICS")
    print("=" * 60)
    print(f"Unique Companies: {analysis['unique_companies']}")
    print(f"Unique Locations: {analysis['unique_locations']}")
    
    if analysis['companies']:
        print(f"\nTop 3 Companies:")
        for i, (company, count) in enumerate(list(analysis['companies'].items())[:3], 1):
            print(f"  {i}. {company} ({count} jobs)")
    
    if analysis['locations']:
        print(f"\nTop 3 Locations:")
        for i, (location, count) in enumerate(list(analysis['locations'].items())[:3], 1):
            print(f"  {i}. {location} ({count} jobs)")
    
    print("\n🎉 Job search and report generation completed successfully!")
    print("💡 Tip: Open the HTML report in your browser for the best viewing experience.")

# Usage examples and configurations
if __name__ == "__main__":
    # Example 1: Basic usage with default settings
    main()
    
    # Example 2: Custom search parameters
    # jobs = search_linkedin_jobs("Software Engineer", "San Francisco", wait_time=10)
    # if jobs:
    #     # Generate HTML report only
    #     html_report = generate_report(jobs, "Software Engineer", "San Francisco", "html")
    #     save_report(html_report, "Software Engineer", "San Francisco", "html")
    
    # Example 3: Generate reports from existing job data
    # Uncomment if you have saved job data and want to regenerate reports
    # try:
    #     with open('saved_jobs.json', 'r') as f:
    #         saved_jobs = json.load(f)
    #     
    #     for format_type in ["html", "txt", "json"]:
    #         report = generate_report(saved_jobs, "Data Analyst", "", format_type)
    #         save_report(report, "Data Analyst", "", format_type)
    # except FileNotFoundError:
    #     print("No saved job data found")

# Additional utility functions
def batch_search_jobs(job_titles, locations=None, wait_time=5):
    """
    Perform batch job searches for multiple job titles and locations.
    
    Args:
        job_titles (list): List of job titles to search
        locations (list): List of locations to search (optional)
        wait_time (int): Wait time between searches
    
    Returns:
        dict: Dictionary with search results for each combination
    """
    results = {}
    locations = locations or [""]
    
    for job_title in job_titles:
        for location in locations:
            search_key = f"{job_title}_{location}" if location else job_title
            print(f"\n🔍 Searching for: {job_title} {f'in {location}' if location else ''}")
            
            jobs = search_linkedin_jobs(job_title, location, wait_time)
            results[search_key] = {
                'job_title': job_title,
                'location': location,
                'jobs': jobs,
                'count': len(jobs)
            }
            
            # Generate individual reports
            if jobs:
                for format_type in ["html", "txt"]:
                    report = generate_report(jobs, job_title, location, format_type)
                    save_report(report, job_title, location, format_type)
    
    return results

def compare_job_searches(search_results):
    """
    Compare results from multiple job searches.
    
    Args:
        search_results (dict): Results from batch_search_jobs()
    
    Returns:
        str: Comparison report
    """
    comparison_report = f"""
{'='*80}
                      JOB SEARCH COMPARISON REPORT
{'='*80}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SEARCH OVERVIEW:
{'-'*40}
"""
    
    for search_key, data in search_results.items():
        location_text = f"in {data['location']}" if data['location'] else ''
        comparison_report += f"{data['job_title']} {location_text}: {data['count']} jobs\n"

    
    comparison_report += f"\n{'='*80}\n"
    
    return comparison_report

# Configuration for different job search scenarios
SEARCH_CONFIGURATIONS = {
    'data_roles': {
        'job_titles': ['Data Analyst', 'Data Scientist', 'Business Analyst'],
        'locations': ['New York', 'San Francisco', 'Chicago'],
        'output_formats': ['html', 'txt']
    },
    'tech_roles': {
        'job_titles': ['Software Engineer', 'Full Stack Developer', 'DevOps Engineer'],
        'locations': ['Seattle', 'Austin', 'Boston'],
        'output_formats': ['html', 'json']
    },
    'marketing_roles': {
        'job_titles': ['Marketing Manager', 'Digital Marketing Specialist', 'Content Manager'],
        'locations': ['Los Angeles', 'Miami', 'Denver'],
        'output_formats': ['html', 'txt', 'json']
    }
}

def run_predefined_search(search_type):
    """
    Run a predefined search configuration.
    
    Args:
        search_type (str): Type of search from SEARCH_CONFIGURATIONS
    """
    if search_type not in SEARCH_CONFIGURATIONS:
        print(f"❌ Invalid search type. Available types: {list(SEARCH_CONFIGURATIONS.keys())}")
        return
    
    config = SEARCH_CONFIGURATIONS[search_type]
    print(f"🚀 Running {search_type} job search configuration...")
    
    # Perform batch search
    results = batch_search_jobs(config['job_titles'], config['locations'])
    
    # Generate comparison report
    comparison = compare_job_searches(results)
    
    # Save comparison report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_filename = f"job_search_comparison_{search_type}_{timestamp}.txt"
    
    with open(comparison_filename, 'w', encoding='utf-8') as f:
        f.write(comparison)
    
    print(f"📊 Comparison report saved to: {comparison_filename}")

# Example usage for predefined searches:
# run_predefined_search('data_roles')
# run_predefined_search('tech_roles')
# run_predefined_search('marketing_roles')
