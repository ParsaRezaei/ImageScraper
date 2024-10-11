
# Image Scraper and Downloader

This Python script scrapes and downloads images from search results using the specified search terms. It uses threading for parallel processing to find URLs and download images efficiently. The script also includes mechanisms to avoid downloading duplicate images by comparing their hashes.

## Features

- Multi-threaded URL scraping and image downloading.
- Avoids downloading duplicate images using hash comparison.
- Automatic retry and exponential backoff for failed requests.
- Displays real-time progress using a progress bar.
- Skips failed domains after multiple download attempts.

## Prerequisites

- Python 3.x
- `requests` library
- `beautifulsoup4` library
- `tqdm` library

You can install the required packages with:
```bash
pip install requests beautifulsoup4 tqdm
```

## How It Works

1. **Search Terms**: The script uses a list of predefined search terms (e.g., "tesla coils", "plasma globe") to scrape images from the web.
2. **Threading**: The script uses multiple threads to perform web scraping and image downloading concurrently for better performance.
3. **Progress Tracking**: A progress bar is displayed in the terminal to track the download progress in real time.
4. **Hash Check**: The script calculates the hash of each downloaded image to prevent downloading duplicates.
5. **Retry Mechanism**: Failed requests are retried up to 5 times using exponential backoff.

## Usage

1. Clone or download the repository.
2. Install the required libraries using the command:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script:
   ```bash
   python imageScraper.py
   ```

   By default, the images are saved in the `images` folder, which will be created if it doesn't exist.

## Configuration

- `NUM_DOWNLOAD_THREADS`: Number of threads for downloading images. Default is 3.
- `SEARCH_TERMS`: List of search terms used for image scraping.
- `NUM_FIND_THREADS`: Number of threads for finding image URLs based on the number of search terms.

## Output

The downloaded images are stored in separate folders based on their search term. Duplicate images are automatically removed.

## Notes

- Ensure you have a stable internet connection while running the script.
- The script uses the Bing search engine to find images.

## Example

Here is an example of the folder structure after running the script:

```
images/
│
├── tesla_coils/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
│
├── plasma_globe/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
│
└── high_voltage_experiments/
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```

## License

This project is licensed under the MIT License. Feel free to use and modify it as you see fit.
