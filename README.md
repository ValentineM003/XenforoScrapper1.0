# XenforoScrapper1.0

# This script automates the process of scraping posts from a source forum and replicating them to a destination forum using Selenium. It is designed to handle login, scrape content, filter out blacklisted content, and post the replicated content in a specified format.
# it comes with other programs to make and scrape Thread links and names.

Configuration
To use this script, you need to configure several variables and file paths:

# Credentials:

source_username: Your username for the source forum.
source_password: Your password for the source forum.
destination_username: Your username for the destination forum.
destination_password: Your password for the destination forum.

# URLs:
destination_success_url: The URL to navigate to after successfully logging in to the destination forum.
destination_login_url: The login URL for the destination forum.
source_success_url: The URL to navigate to after successfully logging in to the source forum.
source_login_url: The login URL for the source forum.
Blacklist File:

BLACKLIST_FILE_PATH: Path to a text file containing sentences or phrases to be filtered out from the scraped content.
Source and Destination Files:

source_file_path: Path to a text file containing URLs of the source threads.
destination_file_path: Path to a text file containing URLs of the destination threads.
