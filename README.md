# QubePayAutoBlogger

# Blog Poster Automation Script

This project automates the process of creating and posting blogs to a WordPress site. The script uses:
- **Python** for scripting.
- **SerpAPI** for fetching relevant web content.
- **Groq API with LLaMA** for generating blog titles and content.
- **WordPress REST API** for publishing posts, including categories.

---

## Current Features

1. **Search Integration**:
   - Uses SerpAPI to gather the latest information on relevant topics like IELTS preparation, English language schools, and general English programs.

2. **Content Generation**:
   - Employs Groq API with LLaMA to generate blog content and titles dynamically.
   - Ensures the title contains the keyword "ELCPP."

3. **WordPress Integration**:
   - Publishes posts to a WordPress site.
   - Assigns categories to the posts based on provided category IDs.

4. **Debugging and Logging**:
   - Includes detailed debug logs for troubleshooting.

---

## Usage

### Running the Script
1. Create python venv 
    ```bash
    python3 -m venv venv
    ```

2. Activate your virtual environment:
   ```bash
   source /path/to/virtual/environment/bin/activate
   ```

3. Install Required packages
    ```bash
    pip install -r requirements.txt
    ```

3. Run the script:
   ```bash
   python blog_poster.py
   ```