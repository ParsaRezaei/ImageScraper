import os
import requests
from bs4 import BeautifulSoup
import re
import time
import threading
from queue import Queue
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
from urllib.parse import urlparse
import hashlib

# Global configuration variables

NUM_DOWNLOAD_THREADS = 3
SEARCH_TERMS = ["tesla coils", "tesla coil", "plasma globe", "high voltage experiments"]
NUM_FIND_THREADS = len(SEARCH_TERMS)

# List to store domains to skip
skipped_domains = set()
# Set to store downloaded image URLs and hashes to avoid duplicates
downloaded_images = set()
downloaded_hashes = set()
# Queues for finding URLs and downloading images
url_queue = Queue()
download_queue = Queue()

# Lock for thread-safe operations
lock = threading.Lock()

# Function to create a valid filename
def valid_filename(filename):
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

# Function to calculate the hash of a file
def calculate_file_hash(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to find image URLs
def find_urls_worker():
    while not url_queue.empty():
        term = url_queue.get()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        query = term.replace(' ', '+')
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            page_num = 1
            while True:  # Loop until no more images are found
                url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2&first={page_num * 20}&tsc=ImageBasicHover"
                response = session.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    img_tags = soup.find_all('a', {'class': 'iusc'})
                    if not img_tags:
                        break  # Exit loop if no more images are found
                    for img_tag in img_tags:
                        # Extract the image URL from the m attribute
                        m = img_tag.get('m')
                        if m:
                            m = re.search(r'"murl":"(.*?)"', m)
                            alt_text = img_tag.get('alt', '').strip()
                            if m:
                                img_url = m.group(1)
                                with lock:
                                    if img_url in downloaded_images:
                                        continue  # Skip if the image URL has already been downloaded
                                    downloaded_images.add(img_url)
                                term_folder = os.path.join(save_folder, valid_filename(term))
                                if not os.path.exists(term_folder):
                                    os.makedirs(term_folder)
                                download_queue.put((img_url, term_folder, alt_text))
                                # Adding delay to prevent rate limiting
                                time.sleep(1.0)  # Increased delay
                else:
                    break  # Exit loop if request fails
                page_num += 1
        except requests.exceptions.RequestException:
            with lock:
                progress_bar.set_postfix_str(f"Request failed for term '{term}'")
        finally:
            url_queue.task_done()

# Function to download an image with retry mechanism
def download_image_worker():
    while True:
        url, folder, alt_text = download_queue.get()
        if url is None:
            break
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        domain = re.search(r'https?://([^/]+)', url).group(1)
        if domain in skipped_domains:
            download_queue.task_done()
            continue

        for attempt in range(5):  # Increased retry count
            try:
                response = requests.get(url, headers=headers, stream=True, timeout=10)
                if response.status_code == 200:
                    # Use the alt text if available, otherwise use the image name from the URL
                    if alt_text:
                        filename = valid_filename(alt_text + '.jpg')
                    else:
                        path = urlparse(url).path
                        image_name = os.path.basename(path)
                        filename = valid_filename(image_name)
                    filepath = os.path.join(folder, filename)
                    # Save the image
                    with open(filepath, 'wb') as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                    # Calculate hash and check for duplicates
                    file_hash = calculate_file_hash(filepath)
                    with lock:
                        if file_hash in downloaded_hashes:
                            os.remove(filepath)  # Remove duplicate file
                        else:
                            downloaded_hashes.add(file_hash)
                            progress_bar.update(1)
                            progress_bar.set_postfix_str(f"Downloaded: {filename}")
                    break
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.RequestException:
                if attempt < 4:
                    time.sleep(2 ** attempt)  # Exponential backoff
        else:
            # If all retries fail, add domain to the skipped list
            with lock:
                skipped_domains.add(domain)
                progress_bar.set_postfix_str(f"Failed after 5 attempts for URL: {url}")
        download_queue.task_done()

# Function to update progress
def update_progress(progress_bar):
    while True:
        with lock:
            progress_bar.n = len(downloaded_images)
            progress_bar.refresh()
        time.sleep(1)
        if all(not t.is_alive() for t in threads):
            break

if __name__ == "__main__":
    # Folder to save the images
    save_folder = "images"
    # Create the folder if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Populate the URL queue with search terms
    for term in SEARCH_TERMS:
        url_queue.put(term)

    threads = []

    # Start the URL finder worker threads
    for _ in range(NUM_FIND_THREADS):
        t = threading.Thread(target=find_urls_worker)
        t.start()
        threads.append(t)

    # Start the download worker threads
    for _ in range(NUM_DOWNLOAD_THREADS):
        t = threading.Thread(target=download_image_worker)
        t.start()
        threads.append(t)

    with tqdm(total=url_queue.qsize() + download_queue.qsize(), desc="Progress", unit=' imgs', dynamic_ncols=True) as progress_bar:
        # Start a thread to update the progress
        progress_thread = threading.Thread(target=update_progress, args=(progress_bar,))
        progress_thread.start()

        # Wait for all tasks in the queues to be processed
        while not url_queue.empty() or not download_queue.empty() or any(t.is_alive() for t in threads):
            time.sleep(0.5)

        # Stop the worker threads
        for _ in range(NUM_DOWNLOAD_THREADS):
            download_queue.put(None)
        for t in threads:
            t.join()
        progress_thread.join()