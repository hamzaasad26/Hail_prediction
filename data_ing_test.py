import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image
import io

# Server configuration
DATA_SERVER = "http://203.135.4.150:3333/images"
TEST_DATE = "2025-06-20"
EXPECTED_CHANNELS = [
    "IR_016", "IR_039", "IR_087", "IR_097", "IR_108", "IR_120", "IR_134",
    "WV_062", "WV_073", "VIS_006", "VIS_008", "HRV"
]
SUPPORTED_EXTENSIONS = ("webp", "bmp", "png", "jpg", "jpeg", "tiff")

def fetch_directory_listing(date):
    """Fetch the directory listing for a given date."""
    date_url = f"{DATA_SERVER}/{date}/"
    print(f"Requesting URL: {date_url}")
    try:
        response = requests.get(date_url, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response content length: {len(response.text)}")
        print(f"Raw response (first 1000 chars):\n{response.text[:1000]}")
        return response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"Error fetching directory listing: {e}")
        return None

def parse_directory_listing(html_content):
    """Parse the HTML directory listing to extract image files."""
    if not html_content:
        return [], []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    image_files = {}
    unmatched_files = []
    
    # Find all <a> tags with href attributes
    links = soup.find_all('a', href=True)
    print(f"Found {len(links)} links in directory listing")
    
    for link in links:
        filename = urllib.parse.unquote(link['href'])  # Decode URL-encoded characters
        # Check if file has a supported extension
        if any(filename.lower().endswith(f".{ext}") for ext in SUPPORTED_EXTENSIONS):
            print(f"Processing file: {filename}")
            # Extract image type
            type_match = re.match(r'^(IR_\d{2,3}|WV_\d{3}|VIS_\d{3}|HRV)', filename, re.IGNORECASE)
            if type_match:
                image_type = type_match.group(1).upper()
                # Extract time from filename
                time_match = re.search(r'\[(\d{2}-\d{2})\]', filename)
                time_str = time_match.group(1) if time_match else "00-00"
                
                if image_type not in image_files:
                    image_files[image_type] = []
                image_files[image_type].append({
                    'filename': filename,
                    'time': time_str,
                    'url': f"{DATA_SERVER}/{TEST_DATE}/{urllib.parse.quote(filename)}"
                })
                print(f"Added {image_type} file: {filename}")
            else:
                unmatched_files.append(filename)
                print(f"Skipping invalid image type: {filename}")
    
    if unmatched_files:
        print(f"Unmatched files: {unmatched_files}")
    
    return image_files, unmatched_files

def download_and_verify_image(url):
    try:
        print(f"Attempting to download: {url}")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            if len(response.content) < 1000:
                print(f"Skipping small file ({len(response.content)} bytes): {url}")
                return False
            print(f"Successfully downloaded {len(response.content)} bytes")
            image = Image.open(io.BytesIO(response.content))
            print(f"Image size: {image.size}, mode: {image.mode}")
            # Save image for inspection
            with open("test_image.bmp", "wb") as f:
                f.write(response.content)
            print("Saved image as test_image.bmp")
            return True
        else:
            print(f"HTTP Error {response.status_code} downloading from {url}")
            return False
    except Exception as e:
        print(f"Error downloading/processing image from {url}: {e}")
        return False

def main():
    """Main function to debug data reading."""
    print(f"Debugging data read for date: {TEST_DATE}")
    
    # Fetch directory listing
    html_content = fetch_directory_listing(TEST_DATE)
    if not html_content:
        print("Failed to fetch directory listing. Exiting.")
        return
    
    # Parse directory listing
    image_files, unmatched_files = parse_directory_listing(html_content)
    print(f"Image types found: {list(image_files.keys())}")
    
    # Get latest images for each type
    latest_images = {}
    for img_type, files in image_files.items():
        if files:
            latest = max(files, key=lambda x: x['time'])
            latest_images[img_type] = latest
            print(f"Latest {img_type}: {latest['filename']} at {latest['time']}")
    
    print(f"Final latest_images: {list(latest_images.keys())}")
    
    # Test downloading one image
    if latest_images:
        sample_type = next(iter(latest_images))
        sample_url = latest_images[sample_type]['url']
        print(f"Testing download for: {sample_url}")
        success = download_and_verify_image(sample_url)
        if success:
            print("Successfully verified sample image.")
        else:
            print("Failed to verify sample image.")
    else:
        print("No valid images found to test download.")

if __name__ == "__main__":
    main()