import os
import requests
import re
import json
import datetime
from dotenv import load_dotenv
from groq import Groq
from serpapi import GoogleSearch
import base64

# ----------------------------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# ----------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

WP_APP_KEY = os.getenv("WP_APP_KEY")
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://www.qubepay.com/wp-json/wp/v2")
GROQ_API_URL = os.getenv("GROQ_API_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")

# text to image keys

CLOUDFLARE_API_URL = os.getenv("CLOUDFLARE_API_URL")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
OUTPUT_DIR = os.getcwd()  # Saves in the current directory
IMG_NAME = "QubePay Online Payments"  # Name of the image file
print("[DEBUG] Loaded WP_APP_KEY:", WP_APP_KEY)
print("[DEBUG] Loaded WP_BASE_URL:", WP_BASE_URL)
print("[DEBUG] Loaded SERP_API_KEY:", SERP_API_KEY)

# ----------------------------------------------------------------------
# 2. SEARCH LOGIC USING SERPAPI
# ----------------------------------------------------------------------

def google_search(query, num_rslts=1, lang='en'):
    print(f"[DEBUG] Starting SerpAPI search for query: '{query}' with {num_rslts} results...")
    search_results = []

    params = {
        "engine": "google",
        "q": query,
        "num": num_rslts,
        "hl": lang,
        "api_key": SERP_API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        for result in results.get("organic_results", []):
            item = {
                "title": result.get("title"),
                "link": result.get("link"),
                "description": result.get("snippet", "No description available")
            }
            search_results.append(item)
            print(f"[DEBUG] Found result: {item}")
    except Exception as e:
        print(f"[ERROR] Error occurred during SerpAPI search: {e}")

    return search_results

# ----------------------------------------------------------------------
# 3. GATHER DATA (SEARCH THE WEB)
# ----------------------------------------------------------------------

def gather_latest_english_learning_info():
    print("[DEBUG] Gathering latest English learning info...")
    combined_results = []
    # change these queries to match the content you want to generate
    queries = [
        "Online Payments",
        "Fintech News",
    ]

    for q in queries:
        print(f"[DEBUG] Processing query: {q}")
        results = google_search(q, num_rslts=5, lang='en')
        print(f"[DEBUG] Query '{q}' returned {len(results)} results.")
        combined_results.extend(results)

    summary_list = []
    for r in combined_results:
        snippet = f"Title: {r['title']} | Desc: {r['description']} | Link: {r['link']}"
        print(f"[DEBUG] Adding snippet: {snippet}")
        summary_list.append(snippet)

    summary_text = "\n".join(summary_list)
    print("[DEBUG] Combined search results into summary text.")
    return summary_text

# ----------------------------------------------------------------------
# 4. GENERATE CONTENT AND TITLE VIA LLM (Using Groq with LLAMA)
# ----------------------------------------------------------------------


def generate_blog_post_content_and_title(latest_info):
    print("[DEBUG] Generating blog post content and title via LLM...")
    client = Groq()

    # Introduce variability by requesting unique and creative title formulations
    prompt = f"""
    You are a professional content writer creating a unique blog post for QubePay, an Online Payments Provider.
    The company offers various patment solutions for all business types.

    Using the latest information provided:
    {latest_info}

    Write an engaging blog post that:
    - Mentions "QubePay Online Payments" (QubePay is the company name).
      and other relevant keywords for SEO.
    - Has a friendly and promotional tone to appeal to prospective students.
    - Concludes with a call-to-action encouraging readers to contact for more details.

    Additionally, generate a unique and catchy blog post title that:
    - Includes "QubePay" and is SEO-friendly.
    - Reflects the blog post content.
    - Avoid repetition of previously generated titles, make unique titles based on the blog post content and {latest_info}.

    Format your output strictly as:
    Title: [Unique blog post title]
    Content: [Engaging blog post content]
    """

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.9,  # Higher creativity
            max_tokens=1024,
        )

        print("[DEBUG] LLM Response:", response)
        generated_text = response.choices[0].message.content
        print("[DEBUG] Successfully generated blog content.")

        # Extract title and content
        if "Title:" in generated_text and "Content:" in generated_text:
            title = generated_text.split("Title:")[1].split("Content:")[0].strip()
            content = generated_text.split("Content:")[1].strip()
        else:
            title = "QubePay Blog Post"
            content = generated_text

        print(f"[DEBUG] Generated Title: {title}")
        print(f"[DEBUG] Blog Content Preview: {content[:500]}...")  # Preview the first 500 characters
        return title, content

    except Exception as e:
        print(f"[ERROR] Error generating blog content with Groq LLM: {e}")
        return "QubePay Blog Post", "An error occurred while generating text."


# ----------------------------------------------------------------------
# 5. CREATE WORDPRESS POST (via Basic Authentication)
# ----------------------------------------------------------------------

def create_wp_post(title, content, category_ids=None, featured_media_id=None, meta_description=None):
    """
    Creates a WordPress blog post and sets a custom meta field for the Yoast SEO meta description.

    Args:
        title (str): The title of the post.
        content (str): The content of the post.
        category_ids (list): List of category IDs for the post.
        featured_media_id (int): Media ID for the featured image.
        meta_description (str): Meta description for the post.

    Returns:
        int: The ID of the created post, or raises an exception if creation fails.
    """
    print("[DEBUG] Creating WordPress post...")
    posts_url = f"{WP_BASE_URL}/posts"

    headers = {
        "Authorization": f"Basic {base64.b64encode(WP_APP_KEY.encode()).decode()}",
        "Content-Type": "application/json"
    }

    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "meta": {
            "_yoast_wpseo_metadesc": meta_description  # Save custom field for meta description
        }
    }

    if category_ids:
        post_data["categories"] = category_ids

    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    try:
        response = requests.post(posts_url, headers=headers, json=post_data)
        response.raise_for_status()
        post_response = response.json()
        post_id = post_response.get("id")
        print(f"[DEBUG] Successfully created post with ID: {post_id}")
        return post_id
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] HTTP Error while creating post: {e}")
        if response is not None:
            print(f"[DEBUG] WordPress Response: {response.text}")
        raise



# ----------------------------------------------------------------------
# 6. GENERATE & SAVE IMAGE LOCALLY (Using Cloudflare AI)
# ----------------------------------------------------------------------

def generate_and_save_image(prompt=None, output_dir=OUTPUT_DIR):

    client = Groq()

    # Default prompt if no dynamic prompt is provided
    default_prompt = "Generate an image of online payments for a fintech blog post."

    # Use Groq LLM to generate a more detailed prompt if no custom prompt is provided
    if not prompt:
        try:
            llm_prompt = """
            Create a detailed and unique image prompt for an AI-generated image. 
            The image should depict a bustling modern fintech environment, showcasing online payment solutions. 
            Include elements such as a diverse group of people using smartphones and laptops for transactions, 
            digital payment icons floating in the background, a sleek payment terminal, and a virtual dashboard 
            displaying financial analytics. The scene should convey innovation, connectivity, and a futuristic 
            approach to financial technology.
            """
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": llm_prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.9,
                max_tokens=512,
            )
            # Extract the generated prompt from LLM response
            prompt = response.choices[0].message.content.strip()
            print("[DEBUG] Generated Prompt from LLM:", prompt)

        except Exception as e:
            print("[ERROR] Failed to generate prompt with Groq LLM. Falling back to default prompt.", str(e))
            prompt = default_prompt

    # Ensure the prompt is a single line for API compatibility
    prompt = " ".join(prompt.split())


    print("[DEBUG] Sending API Request:")
    print("[DEBUG] URL:", CLOUDFLARE_API_URL)
    print("[DEBUG] Payload:", prompt)
    

    # Hardcode the prompt for testing
    print(f"[DEBUG] Generating image for hardcoded prompt: {prompt}")
    
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt
    }

    try:
        response = requests.post(CLOUDFLARE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()

        # Debugging: Print the raw response
        print(f"[DEBUG] Cloudflare API Response: {response_data}")

        # Check if the response indicates success
        if response_data.get("success", False):
            result = response_data.get("result")
            
            # Debugging: Print the type and structure of 'result'
            print(f"[DEBUG] Type of 'result': {type(result)}")
            print(f"[DEBUG] Content of 'result': {result}")

            if isinstance(result, str):
                # Case: Result is a base64-encoded string
                base64_image = result
            elif isinstance(result, dict):
                # Case: Result is a dictionary with nested image data
                base64_image = result.get("image")
                if not base64_image:
                    print("[ERROR] No 'image' key found in result.")
                    return None
            else:
                print("[ERROR] Unexpected 'result' format:", result)
                return None
            


            # Save the image
            output_file_path = os.path.join(output_dir, f"{IMG_NAME.replace(' ', '_')}.png")
            with open(output_file_path, "wb") as img_file:
                img_file.write(base64.b64decode(base64_image))

            print(f"[DEBUG] Image saved successfully: {output_file_path}")
            return output_file_path
        else:
            print(f"[ERROR] API Error: {response_data.get('errors', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] HTTP Error while generating image: {e}")
    return None


# ----------------------------------------------------------------------
# 7. POST IMAGE TO WORDPRESS MEDIA LIBRARY AND GET ID
# ----------------------------------------------------------------------

def upload_image_to_wordpress(image_path, title, alt_text):
    """
    Uploads an image to WordPress media library.

    Args:
        image_path (str): Path to the image file.
        title (str): Title for the uploaded image.
        alt_text (str): Alt text for the uploaded image.

    Returns:
        int: Media ID of the uploaded image, or None if upload fails.
    """
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file does not exist: {image_path}")
        return None

    print(f"[DEBUG] Uploading image to WordPress: {image_path}")
    media_url = f"{WP_BASE_URL}/media"

    # Encode credentials for basic authentication
    try:
        encoded_auth = base64.b64encode(WP_APP_KEY.encode()).decode()
    except Exception as e:
        print(f"[ERROR] Failed to encode WP_APP_KEY: {e}")
        return None

    headers = {
        "Authorization": f"Basic {encoded_auth}"  # Basic auth encoded as Base64
    }

    # Prepare multipart form data
    files = {
        "file": (os.path.basename(image_path), open(image_path, "rb"), "image/png"),
        "title": (None, title),
        "alt_text": (None, alt_text)
    }

    try:
        response = requests.post(media_url, headers=headers, files=files)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        media_response = response.json()

        print(f"[DEBUG] WordPress Media Response: {media_response}")

        # Extract and return the media ID
        media_id = media_response.get("id")
        if not media_id:
            print("[ERROR] Failed to retrieve media ID from response.")
            return None

        print(f"[DEBUG] Image uploaded successfully. Media ID: {media_id}")
        return media_id
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] HTTP Error while uploading image: {e}")
        if response is not None:
            print(f"[DEBUG] WordPress Response: {response.text}")
        return None
    
# ----------------------------------------------------------------------
# Utility Function to Sanitize Title
# ----------------------------------------------------------------------

def sanitize_title(title):
    """
    Removes unwanted characters like * and " from the post title.
    
    Args:
        title (str): The original title.
    
    Returns:
        str: The sanitized title.
    """
    # Remove * and " characters
    sanitized_title = re.sub(r'[*"]', '', title)
    return sanitized_title.strip()  # Remove leading/trailing whitespace

# ----------------------------------------------------------------------
# 8. MAIN WORKFLOW
# ----------------------------------------------------------------------

def main():
    print("[DEBUG] Starting main workflow...")

    # Step 1: Gather latest info from the web
    latest_info = gather_latest_english_learning_info()
    print(f"[DEBUG] Latest info summary:\n{latest_info}")

    if not latest_info.strip():
        print("[ERROR] No search results returned. Exiting...")
        return

    # Step 2: Generate blog content and title using LLM
    try:
        raw_post_title, blog_content = generate_blog_post_content_and_title(latest_info)
        post_title = sanitize_title(raw_post_title)  # Sanitize the title
        print(f"[DEBUG] Raw Post Title: {raw_post_title}")
        print(f"[DEBUG] Sanitized Post Title: {post_title}")
        print(f"[DEBUG] Generated Blog Content:\n{blog_content}")
    except Exception as e:
        print(f"[ERROR] Failed to generate blog content and title: {e}")
        return

    # Step 3: Generate and save the image locally
    try:
        image_path = generate_and_save_image(post_title)
        print(f"[DEBUG] Image Path: {image_path}")
        if not image_path:
            print("[ERROR] Failed to generate image. Skipping image upload.")
            return
    except Exception as e:
        print(f"[ERROR] Error during image generation: {e}")
        return

    # Step 4: Upload image to WordPress and get Media ID
    try:
        image_title = post_title
        image_alt_text = post_title
        media_id = upload_image_to_wordpress(image_path, image_title, image_alt_text)
        if not media_id:
            print("[ERROR] Failed to upload image. Skipping blog post creation.")
            return
    except Exception as e:
        print(f"[ERROR] Error during image upload: {e}")
        return

    # Step 5: Create WordPress blog post with featured image and meta description
    try:
        category_ids = [180]  # Replace with your actual category ID(s)

        # Extract the first 100 words of the blog content for meta description
        meta_description = " ".join(blog_content.split()[:100])

        # Create the WordPress post
        new_post_id = create_wp_post(
            title=post_title,
            content=blog_content,
            category_ids=category_ids,
            featured_media_id=media_id,
            meta_description=meta_description
        )

        print(f"[DEBUG] Successfully created post please remember to add meta description manually in yoast SEO plugin #{new_post_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create WordPress post: {e}")


if __name__ == "__main__":
    main()
