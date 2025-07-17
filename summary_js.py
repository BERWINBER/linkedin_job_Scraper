import json
import os
import requests
import sys
import argparse
from typing import Dict, Optional
from datetime import datetime
import glob

# =============================================================================
# CONFIGURATION - Choose your LLM provider
# =============================================================================

# Option 1: OLLAMA (LOCAL) - Default
USE_OLLAMA = True
OLLAMA_MODEL = "gemma3:4b"  # You can change to "llama3.1:8b" or other models
OLLAMA_URL = "http://localhost:11434/api/generate"

# Option 2: OPENAI/CHATGPT API
# Uncomment below and add your API key to use ChatGPT
# USE_OPENAI = False
# OPENAI_API_KEY = "your-openai-api-key-here"
# OPENAI_MODEL = "gpt-3.5-turbo"  # or "gpt-4"

# Option 3: GOOGLE GEMINI API
# Uncomment below and add your API key to use Gemini
# USE_GEMINI = False
# GEMINI_API_KEY = "your-gemini-api-key-here"
# GEMINI_MODEL = "gemini-pro"

# =============================================================================
# PROMPT TEMPLATE
# =============================================================================

SUMMARY_PROMPT = """
You are a job analysis expert. Please analyze the following job description and provide a comprehensive summary in MARKDOWN format.

Company: {company_name}
Job Title: {job_title}

Job Description:
{job_description}

Please provide a summary in MARKDOWN format that includes:
1. Key Responsibilities (3-5 main duties)
2. Required Skills & Technologies
3. Experience Level Required
4. Key Qualifications
5. Company/Role Highlights

Format your response using proper markdown with headers, bullet points, and emphasis. Be concise but comprehensive.
Example format:
## Key Responsibilities
- Responsibility 1
- Responsibility 2

## Required Skills & Technologies
- **Primary Skills**: Python, Machine Learning
- **Frameworks**: TensorFlow, PyTorch
- **Tools**: Docker, Kubernetes

## Experience Level Required
- Years of experience needed
- Specific background requirements

## Key Qualifications
- Education requirements
- Certifications needed

## Company/Role Highlights
- Company culture points
- Role benefits and opportunities
"""

class JobSummarizer:
    def __init__(self):
        self.llm_provider = self._determine_llm_provider()
        
    def _determine_llm_provider(self) -> str:
        """Determines which LLM provider to use based on configuration."""
        if USE_OLLAMA:
            return "ollama"
        # elif USE_OPENAI:
        #     return "openai"
        # elif USE_GEMINI:
        #     return "gemini"
        else:
            return "ollama"  # Default fallback

    def find_json_files(self, directory: str = ".") -> list:
        """Finds all JSON files that match the job scraper pattern."""
        pattern = os.path.join(directory, "job_*.json")
        json_files = glob.glob(pattern)
        return sorted(json_files, key=os.path.getmtime, reverse=True)  # Latest first

    def read_job_data(self, json_file_path: str) -> Optional[Dict]:
        """Reads job data from JSON file."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Successfully loaded job data from: {json_file_path}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {json_file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None

    def generate_summary_ollama(self, prompt: str) -> Optional[str]:
        """Generates summary using Ollama local LLM."""
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            print(f"🤖 Generating summary using Ollama ({OLLAMA_MODEL})...")
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                print(f"❌ Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to Ollama. Make sure Ollama is running locally.")
            print("💡 Start Ollama with: ollama serve")
            return None
        except Exception as e:
            print(f"❌ Error with Ollama: {e}")
            return None

    # UNCOMMENT AND CONFIGURE BELOW FOR OPENAI/CHATGPT
    # def generate_summary_openai(self, prompt: str) -> Optional[str]:
    #     """Generates summary using OpenAI ChatGPT API."""
    #     try:
    #         import openai
    #         openai.api_key = OPENAI_API_KEY
    #         
    #         print(f"🤖 Generating summary using OpenAI ({OPENAI_MODEL})...")
    #         response = openai.ChatCompletion.create(
    #             model=OPENAI_MODEL,
    #             messages=[
    #                 {"role": "system", "content": "You are a job analysis expert."},
    #                 {"role": "user", "content": prompt}
    #             ],
    #             max_tokens=1000,
    #             temperature=0.7
    #         )
    #         
    #         return response.choices[0].message.content.strip()
    #     except Exception as e:
    #         print(f"❌ Error with OpenAI: {e}")
    #         return None

    # UNCOMMENT AND CONFIGURE BELOW FOR GOOGLE GEMINI
    # def generate_summary_gemini(self, prompt: str) -> Optional[str]:
    #     """Generates summary using Google Gemini API."""
    #     try:
    #         import google.generativeai as genai
    #         genai.configure(api_key=GEMINI_API_KEY)
    #         
    #         print(f"🤖 Generating summary using Gemini ({GEMINI_MODEL})...")
    #         model = genai.GenerativeModel(GEMINI_MODEL)
    #         response = model.generate_content(prompt)
    #         
    #         return response.text.strip()
    #     except Exception as e:
    #         print(f"❌ Error with Gemini: {e}")
    #         return None

    def generate_summary(self, job_data: Dict) -> Optional[str]:
        """Generates job summary using the configured LLM provider."""
        # Extract required data
        company_name = job_data.get("company_name", "Unknown Company")
        job_title = job_data.get("job_title", "Unknown Position")
        job_description = job_data.get("job_description_text", "")
        
        if not job_description:
            print("❌ No job description found in the data.")
            return None
        
        # Create prompt
        prompt = SUMMARY_PROMPT.format(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description
        )
        
        # Generate summary based on provider
        if self.llm_provider == "ollama":
            return self.generate_summary_ollama(prompt)
        # elif self.llm_provider == "openai":
        #     return self.generate_summary_openai(prompt)
        # elif self.llm_provider == "gemini":
        #     return self.generate_summary_gemini(prompt)
        else:
            print(f"❌ Unknown LLM provider: {self.llm_provider}")
            return None

    def save_summary(self, job_data: Dict, summary: str) -> str:
        """Saves the generated summary to a markdown file."""
        # Create filename based on job title
        job_title = job_data.get("job_title", "Unknown_Job")
        safe_title = "".join(c for c in job_title if c.isalnum() or c in " -_").rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_summary_{safe_title}_{timestamp}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Write markdown header
                f.write(f"# Job Summary: {job_data.get('job_title', 'Unknown Position')}\n\n")
                
                # Job details table
                f.write("## Job Details\n\n")
                f.write("| Field | Value |\n")
                f.write("|-------|-------|\n")
                f.write(f"| **Company** | {job_data.get('company_name', 'N/A')} |\n")
                f.write(f"| **Position** | {job_data.get('job_title', 'N/A')} |\n")
                f.write(f"| **Location** | {job_data.get('location', 'N/A')} |\n")
                f.write(f"| **Salary** | {job_data.get('salary_info', 'N/A')} |\n")
                f.write(f"| **Job Type** | {job_data.get('job_type', 'N/A')} |\n")
                f.write(f"| **Seniority** | {job_data.get('seniority_level', 'N/A')} |\n")
                f.write(f"| **Posted** | {job_data.get('posted_date', 'N/A')} |\n")
                f.write(f"| **Source** | [LinkedIn Job]({job_data.get('url', 'N/A')}) |\n")
                f.write(f"| **Summary Generated** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |\n")
                f.write(f"| **LLM Provider** | {self.llm_provider} |\n\n")
                
                # Job criteria if available
                if job_data.get('job_criteria'):
                    f.write("## Job Criteria\n\n")
                    for criterion in job_data.get('job_criteria', []):
                        f.write(f"- {criterion}\n")
                    f.write("\n")
                
                # AI Generated Summary
                f.write("---\n\n")
                f.write("# AI Generated Summary\n\n")
                f.write(summary)
                f.write("\n\n---\n\n")
                
                # Footer
                f.write("*This summary was generated using AI analysis of the job description.*\n")
            
            print(f"💾 Markdown summary saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving summary: {e}")
            return ""

    def display_markdown_in_terminal(self, markdown_content: str):
        """Display markdown content in terminal with basic formatting."""
        lines = markdown_content.split('\n')
        
        for line in lines:
            # Headers
            if line.startswith('# '):
                print(f"\n{'='*60}")
                print(f"🎯 {line[2:].upper()}")
                print(f"{'='*60}")
            elif line.startswith('## '):
                print(f"\n📋 {line[3:].upper()}")
                print(f"{'-'*40}")
            elif line.startswith('### '):
                print(f"\n🔸 {line[4:]}")
            # Bold text
            elif '**' in line:
                # Simple bold formatting for terminal
                formatted_line = line.replace('**', '').replace('*', '')
                print(f"  {formatted_line}")
            # Bullet points
            elif line.startswith('- '):
                print(f"  • {line[2:]}")
            # Table rows
            elif line.startswith('|') and '|' in line[1:]:
                # Simple table formatting
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) == 2:
                    print(f"  {cells[0]:<20} | {cells[1]}")
            # Horizontal rules
            elif line.startswith('---'):
                print(f"\n{'─'*60}")
            # Regular text
            elif line.strip():
                print(f"  {line}")
            # Empty lines
            else:
                print()

    def print_summary(self, job_data: Dict, summary: str):
        """Prints the summary to console with markdown formatting."""
        print("\n" + "="*60)
        print("🤖 AI GENERATED JOB SUMMARY (MARKDOWN)")
        print("="*60)
        
        # Create full markdown content
        markdown_content = f"""# Job Summary: {job_data.get('job_title', 'Unknown Position')}

## Job Details

| Field | Value |
|-------|-------|
| **Company** | {job_data.get('company_name', 'N/A')} |
| **Position** | {job_data.get('job_title', 'N/A')} |
| **Location** | {job_data.get('location', 'N/A')} |
| **Salary** | {job_data.get('salary_info', 'N/A')} |

---

{summary}
"""
        
        self.display_markdown_in_terminal(markdown_content)
        print("="*60)

    def run(self, json_file_path: str = None, display_only: bool = False, open_markdown: bool = False):
        """Main method to run the job summarizer."""
        # If no file specified, find the latest JSON file
        if not json_file_path:
            json_files = self.find_json_files()
            if not json_files:
                print("❌ No job JSON files found in current directory.")
                print("💡 Make sure you have run the LinkedIn scraper first.")
                return
            
            json_file_path = json_files[0]
            print(f"📄 Using latest job file: {json_file_path}")
        
        # Read job data
        job_data = self.read_job_data(json_file_path)
        if not job_data:
            return
        
        # Generate summary
        summary = self.generate_summary(job_data)
        if not summary:
            print("❌ Failed to generate summary.")
            return
        
        # Display summary
        self.print_summary(job_data, summary)
        
        # Save summary unless display-only mode
        if not display_only:
            summary_file = self.save_summary(job_data, summary)
            
            if summary_file:
                print(f"\n✅ Process completed successfully!")
                print(f"📄 Markdown summary saved to: {summary_file}")
                
                # Open markdown file if requested
                if open_markdown:
                    self.open_markdown_file(summary_file)
        else:
            print(f"\n✅ Summary displayed (not saved to file)")

    def open_markdown_file(self, filename: str):
        """Opens the markdown file in the default application."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", filename])
            elif system == "Windows":
                subprocess.run(["start", filename], shell=True)
            elif system == "Linux":
                subprocess.run(["xdg-open", filename])
            else:
                print(f"💡 Please open the file manually: {filename}")
                
            print(f"📖 Opened markdown file: {filename}")
        except Exception as e:
            print(f"⚠️ Could not open file automatically: {e}")
            print(f"💡 Please open the file manually: {filename}")

def main():
    """Main function with user interaction and command-line arguments."""
    parser = argparse.ArgumentParser(description='Generate AI summaries from LinkedIn job JSON files')
    parser.add_argument('--file', '-f', type=str, help='Specific JSON file path to process')
    parser.add_argument('--directory', '-d', type=str, default='.', help='Directory to search for JSON files')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode to select from multiple files')
    parser.add_argument('--display-only', action='store_true', help='Only display in terminal, do not save file')
    parser.add_argument('--open-markdown', '-o', action='store_true', help='Open the generated markdown file after creation')
    
    args = parser.parse_args()
    
    print("🤖 Job Description Summarizer with LLM")
    print("="*50)
    
    # Initialize summarizer
    summarizer = JobSummarizer()
    
    # Case 1: Specific file provided
    if args.file:
        if os.path.exists(args.file):
            print(f"📄 Processing specified file: {args.file}")
            summarizer.run(args.file)
        else:
            print(f"❌ File not found: {args.file}")
        return
    
    # Case 2: Search for JSON files in directory
    json_files = summarizer.find_json_files(args.directory)
    
    if not json_files:
        print(f"❌ No job JSON files found in directory: {args.directory}")
        print("💡 Please run the LinkedIn scraper first to generate job data.")
        return
    
    # Show available files
    print(f"📁 Found {len(json_files)} job file(s) in {args.directory}:")
    for i, file in enumerate(json_files, 1):
        print(f"  {i}. {file}")
    
    # Case 3: Interactive mode - let user choose
    if args.interactive and len(json_files) > 1:
        while True:
            try:
                choice = input(f"\n🎯 Select file to process (1-{len(json_files)}) or 'q' to quit: ").strip()
                if choice.lower() == 'q':
                    print("👋 Goodbye!")
                    return
                
                file_index = int(choice) - 1
                if 0 <= file_index < len(json_files):
                    selected_file = json_files[file_index]
                    print(f"📄 Processing selected file: {selected_file}")
                    summarizer.run(selected_file, display_only=args.display_only, open_markdown=args.open_markdown)
                    break
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(json_files)}")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return
    
    # Case 4: Default - process latest file
    else:
        if len(json_files) == 1:
            print(f"\n🎯 Processing the only available file: {json_files[0]}")
        else:
            print(f"\n🎯 Processing latest file: {json_files[0]}")
            print("💡 Use --interactive flag to choose a different file.")
        
        summarizer.run(json_files[0])

if __name__ == "__main__":
    main()
