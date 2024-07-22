import logging
import re
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO)

MAX_LOGIN_ATTEMPTS = 3

# Initialize the global variable for posts_done
posts_done = 0

# Maximum number of attempts to post a message
MAX_POST_ATTEMPTS = 3
# Initialize the index of the last posted source post
last_posted_index = 2


# Source and destination credentials
source_username = #source username
source_password = #source password
destination_username = #destination username
destination_password = #destinationa password

destination_success_url = # Assign a destination url, it'll be the url after you login in to the forum
destination_login_url = # Login url to the destination forum here

source_success_url = # Assign a source url, it'll be the url after you login in to the forum
source_login_url = # Login url to the source forum here

def login(driver, username, password, login_url, success_url):
    attempt = 1

    while attempt <= MAX_LOGIN_ATTEMPTS:
        driver.get(login_url)
        logging.info(f"Opened login page: {login_url}")

        # Check if already logged in
        if is_logged_in(driver):
            logging.info("Already logged in. Continuing...")
            return True

        try:
            username_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = driver.find_element(By.NAME, "password")

            username_field.clear()
            password_field.clear()

            username_field.send_keys(username)
            password_field.send_keys(password)

            password_field.submit()

            logging.info("Submitted login form")

            # Wait for the success URL
            WebDriverWait(driver, 30).until(
                EC.url_to_be(success_url)
            )

            logging.info("Login successful")
            return True

        except TimeoutException:
            logging.error(f"Timeout during login attempt {attempt}/{MAX_LOGIN_ATTEMPTS}. Retrying...")
            attempt += 1
        except Exception as e:
            logging.error(f"Login failed: {e}")
            logging.error(f"Current URL: {driver.current_url}")

            if attempt <= MAX_LOGIN_ATTEMPTS:
                attempt += 1
            else:
                logging.error("Max login attempts reached. Exiting.")
                return False

    logging.error("Failed to login after {} attempts. Exiting.".format(MAX_LOGIN_ATTEMPTS))
    return False


def is_logged_in(driver):
    try:
        # Check if the login element is present on the page
        login_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='blockMessage' and contains(text(), 'You are "
                                                      "already logged in.')]"))
        )
        return login_element is not None
    except TimeoutException:
        return False


def reset_browser(driver):
    try:
        driver.delete_all_cookies()
        logging.info("Deleted all cookies to reset the browser state.")
    except Exception as e:
        logging.error(f"Error resetting the browser: {e}")


def get_number_of_pages(driver, thread_url):
    driver.get(thread_url)

    try:
        # Wait for the pagination element to be present
        pagination = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pageNav-main"))
        )

        # Find all page links
        page_links = pagination.find_elements(By.CLASS_NAME, "pageNav-page")

        # Extract the page numbers
        page_numbers = []

        for link in page_links:
            try:
                page_number = int(link.text)
                page_numbers.append(page_number)
            except ValueError:
                # Handle the case where the text cannot be converted to an integer
                logging.warning(f"Invalid page number format: {link.text}. Skipping.")
                continue

        # Find the maximum page number
        max_page_number = max(page_numbers) if page_numbers else 1

        return max_page_number

    except TimeoutException:
        logging.error("Timeout while analyzing thread pages. Assuming only one page.")
        return 1


def load_blacklist(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            blacklist = {line.strip() for line in file.readlines()}
        return blacklist
    except FileNotFoundError:
        logging.warning("Blacklist file not found. No blacklisted sentences will be checked.")
        return set()


BLACKLIST_FILE_PATH = # path to a txt file that contains any unwanted content to be scrapped
blacklist = load_blacklist(BLACKLIST_FILE_PATH)


def scrape_post_information(driver, source_thread_url, source_username, source_password, login_required=True):
    global post_index
    post_info_list = []

    def extract_text_content(bb_wrapper_element):
        try:
            # Exclude link elements and elements with class bbCodeSpoiler-button-title from the text content
            text_content = bb_wrapper_element.text
            links = bb_wrapper_element.find_elements(By.XPATH, ".//a[@href]")
            spoilers = bb_wrapper_element.find_elements(By.CLASS_NAME, "bbCodeSpoiler-button-title")

            for link in links:
                text_content = text_content.replace(link.text, '').replace(link.get_attribute("href"), '')

            for spoiler in spoilers:
                text_content = text_content.replace(spoiler.text, '')

            return text_content
        except Exception as e:
            logging.error(f"Error extracting text content: {e}")
            return ''

    def extract_links(bb_wrapper_element):
        try:
            # Extract links from the main wrapper element
            unfurl_links = list(set(link.get_attribute("href") for link in
                                    bb_wrapper_element.find_elements(By.XPATH,
                                                                     ".//div[@class='bbCodeBlock bbCodeBlock--unfurl "
                                                                     "js-unfurl fauxBlockLink']//a[@href]")))

            # Check if the link is within bbCodeSpoiler or bbCodeBlock-content divs and exclude them
            external_links = list(set(link.get_attribute("href") for link in
                                      bb_wrapper_element.find_elements(By.XPATH,
                                                                       ".//a[contains(@class,'link--external') and "
                                                                       "not(ancestor::div[contains(@class, 'bbCodeSpoiler')]) and "
                                                                       "not(ancestor::div[contains(@class, 'bbCodeBlock-content')]) and "
                                                                       "@href]")))

            
            prefixes_to_exclude = # Filter out links starting with certain prefixes

            # Remove links that start with excluded prefixes
            unfurl_links = [link for link in unfurl_links if
                            not any(link.startswith(prefix) for prefix in prefixes_to_exclude)]
            external_links = [link for link in external_links if
                              not any(link.startswith(prefix) for prefix in prefixes_to_exclude)]

            # Combine all link types into a dictionary
            return {
                'unfurl_links': unfurl_links,
                'external_links': external_links,
            }

        except Exception as e:
            logging.error(f"Error extracting links: {e}")
            return {
                'unfurl_links': [],
                'external_links': [],
            }



    def extract_images(bb_wrapper_element):
        try:
            # Wait for bbImage elements to be present
            bb_images = WebDriverWait(bb_wrapper_element, 0).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "bbImage"))
            )
            bb_image_links = [image.get_attribute("src") for image in bb_images]
            # Modify the image links
            modified_bb_image_links = [link.replace('.th.jpg', '.md.jpg') for link in bb_image_links]

            return modified_bb_image_links
        except Exception as e:
            logging.error(f"Error extracting images: {e}")
            return []

    def extract_spoiler_info(bb_wrapper_element):
        spoiler_info_list = []

        try:
            spoiler_divs = bb_wrapper_element.find_elements(By.CLASS_NAME, "bbCodeSpoiler")

            for spoiler_div in spoiler_divs:
                try:
                    spoiler_title = spoiler_div.find_element(By.CLASS_NAME, "bbCodeSpoiler-button-title").text.strip()

                    spoiler_links = []
                    spoiler_content = WebDriverWait(spoiler_div, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "bbCodeBlock-content"))
                    )

                    links = spoiler_content.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        spoiler_links.append(link.get_attribute("href"))

                    spoiler_info = {
                        "title": spoiler_title,
                        "links": spoiler_links,
                    }

                    spoiler_info_list.append(spoiler_info)

                except StaleElementReferenceException as e:
                    logging.warning(f"StaleElementReferenceException: {e}. Retrying spoiler extraction.")
                    continue

            # Format spoiler links
            formatted_spoiler_links = []
            for spoiler_info in spoiler_info_list:
                title = spoiler_info.get("title", "")
                links = spoiler_info.get("links", [])
                spoiler_content = "[SPOILER=\"{}\"]{}\n[/SPOILER]".format(title, '\n'.join(links))
                formatted_spoiler_links.append(spoiler_content)

            return formatted_spoiler_links

        except Exception as e:
            logging.error(f"Error extracting spoiler information: {e}")
            return []

    if login_required and not login(driver, source_username, source_password, source_login_url,
                                    source_success_url):
        logging.error("Failed to log in to the source site. Exiting.")
        return post_info_list

    num_pages = get_number_of_pages(driver, source_thread_url)

    for page in range(1, num_pages + 1):
        current_page_url = source_thread_url if page == 1 else f"{source_thread_url}page-{page}"
        driver.get(current_page_url)
        logging.info(f"Opened post page: {current_page_url}")

        try:
            bb_wrapper_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,
                                                     "//article[contains(@class,'message')]//div[contains(@class,"
                                                     "'message-userContent')]//div[contains(@class,'bbWrapper')]"))
            )
            logging.info(f"Number of bb_wrapper_elements on page {page}: {len(bb_wrapper_elements)}")

            # Inside the 'scrape_post_information' function
            for post_index, bb_wrapper_element in enumerate(bb_wrapper_elements, start=2):
                logging.info(f"Processing post {post_index} on page {page}")
                text_content = extract_text_content(bb_wrapper_element)

                # Check if the post has only blacklisted sentence(s)
                contains_only_blacklisted = all(
                    blacklisted_sentence in text_content for blacklisted_sentence in blacklist)

                if contains_only_blacklisted:
                    logging.info(f"Skipping post {post_index} as it contains only blacklisted sentence(s).")
                    continue

                # Remove blacklisted sentences from the text content
                for blacklisted_sentence in blacklist:
                    text_content = text_content.replace(blacklisted_sentence, '')

                # Remove blacklisted sentences from the text content
                text_content = '\n'.join(
                    [sentence for sentence in text_content.split('\n') if sentence not in blacklist])

                links_info = extract_links(bb_wrapper_element)
                unfurl_links = links_info.get('unfurl_links', [])
                external_links = links_info.get('external_links', [])
                bbimages = extract_images(bb_wrapper_element)
                spoiler_info = extract_spoiler_info(bb_wrapper_element)

                post_info = {
                    'text_content': text_content,
                    'unfurl_links': unfurl_links,
                    'external_links': external_links,
                    'bbimage_links': bbimages,
                    'spoiler_info': list(spoiler_info),  # Convert set to list
                }

                post_info_list.append(post_info)

        except Exception as e:
            logging.error(f"Error extracting information for Post {post_index} on Page {page}: {e}")

        except TimeoutException:
            logging.error("Timeout while scraping post information")

    logging.info(f"Number of posts scraped: {len(post_info_list)}")
    return post_info_list

    # Replicate function

def replicate_and_post(driver, source_thread_url, source_username, source_password, destination_username,
                       destination_password, destination_thread_url, is_destination_logged_in=False):
    # Make posts_done global
    global posts_done

    if not is_destination_logged_in:
        scraped_data = scrape_post_information(driver, source_thread_url, source_username, source_password,
                                               login_required=True)
    else:
        scraped_data = scrape_post_information(driver, source_thread_url, source_username, source_password,
                                              login_required=False)

     Login to the source site only if not already logged in
    if not is_destination_logged_in:
        if not login(driver, source_username, source_password, source_login_url,
                     source_success_url):
            logging.error("Failed to log in to the source site. Exiting.")
            return
        else:
            logging.info("Successfully logged in to the source site.")

    # Login to the destination site if not already logged in
    if not is_destination_logged_in:
        if not login(driver, destination_username, destination_password, destination_login_url,
                    destination_success_url ) :
            logging.error("Failed to log in to the destination site. Exiting.")
            return
        else:
            logging.info("Successfully logged in to the destination site.")

    # Navigate to the destination thread URL
    driver.get(destination_thread_url)
    logging.info(f"Opened destination thread: {destination_thread_url}")

    # Iterate through each post from the scraped data
    for post_index, post_info in enumerate(scraped_data, start=2):
        # Skip already posted source posts
        if post_index <= last_posted_index:
            logging.info(f"Skipped already posted Source Post {post_index}")
            continue

        try:
            # Refresh the browser and wait for 5 seconds every 20 posts
            if posts_done % 20 == 0 and posts_done != 0:
                logging.info("Refreshing the browser and waiting for 5 seconds.")
                driver.refresh()
                time.sleep(5)
            # Check if the post has only text content and skip it
            if not any(post_info.get(key) for key in
                       ['bbimage_links', 'saint_links', 'unfurl_links', 'external_links', 'redgif_links',
                        'spoiler_info']):
                logging.info(f"Skipping post {post_index} as it has only text content.")
                continue

            # Replace red gif code with href link
            redgif_pattern = re.compile(r'\[redgif]([^\[\]]+)\[/redgif]')
            text_content = post_info.get('text_content', '')
            redgif_replaced_content = redgif_pattern.sub(lambda match: f"https://www.redgifs.com/{match.group(1)}",
                                                         text_content)
            post_info['text_content'] = redgif_replaced_content

            # Prepare content for posting
            unique_links = set()
            spoiler_links = [link for link in post_info.get('spoiler_info', []) if link.startswith('http')]
            other_links = {
                'unfurl_links': post_info.get('unfurl_links', []),
                'external_links': post_info.get('external_links', []),
                'redgif_links': post_info.get('redgif_links', [])
            }

            # Remove common links from other link categories
            for category, links in other_links.items():
                other_links[category] = [link for link in links if link not in spoiler_links]

            # Check if any external links match spoiler links and remove them
            spoiler_external_matches = set(spoiler_links) & set(other_links['external_links'])
            for link in spoiler_external_matches:
                other_links['external_links'].remove(link)

            # Adjust the content_parts
            content_parts = [
                ' '.join(post_info.get('text_content', '').split()),  # Remove extra spaces
                ''.join([f'[img]{link}[/img]' for link in set(post_info.get('bbimage_links', []))]),
                # Remove duplicates using set
                '\n'.join(post_info.get('spoiler_info', [])),
                '\n'.join(link for link in set(other_links['unfurl_links']) if
                          link not in unique_links and not unique_links.add(link)),
                '\n'.join(other_links['external_links']),  # Include external links

            ]

            content = '\n'.join(content_parts)

            # Locate the contenteditable div for posting
            contenteditable_div = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='fr-element fr-view fr-element-scroll-visible']"))
            )

            # Check if the content is not empty before posting
            if content.strip():
                # Type the content
                contenteditable_div.send_keys(content)

                # Click the "Post reply" button
                post_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Post reply']"))
                )
                post_button.click()
                # Call handle_overlay after clicking the "Post reply" button
                handle_overlay(driver)
                logging.info(f"Posted reply for Source Post {post_index}")

                # Increment the global posts_done variable
                posts_done += 1

                # Wait for the "Post reply" button to become clickable again
                WebDriverWait(driver, 10).until(
                    EC.staleness_of(post_button)  # Wait for the button to become stale
                )

        except ElementClickInterceptedException:
            logging.warning("ElementClickInterceptedException: Overlay detected. Refreshing the browser.")
            # Handle overlay if it's present
            handle_overlay(driver)

            # Wait for a moment after refreshing
            time.sleep(2)

            # Skip to the next post
            continue

        except NoSuchElementException as e:
            logging.error(f"Error during posting for Source Post {post_index}: {e}")

            # Refresh the browser and clear the message box
            logging.warning("Retrying posting.")
            reset_browser(driver)

            # Wait before retrying
            time.sleep(5)
            continue

        except Exception as e:
            logging.error(f"Unhandled error during posting for Source Post {post_index}: {e}")

    logging.info("All posts have been replicated and posted.")


def handle_overlay(driver):
    try:
        overlay_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "overlay-container.is-active"))
        )

        if overlay_container.is_displayed():
            logging.info("Overlay detected. Clearing the message box and refreshing the page.")

            # Clear the message box
            message_box = driver.find_element(By.XPATH, "//div[@class='fr-element fr-view fr-element-scroll-visible']")
            message_box.clear()

            # Wait for a moment after clearing the message box
            time.sleep(2)

            # Refresh the page
            driver.refresh()
            message_box.clear()

            # Wait for the page to load after refresh
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Wait for 5 seconds
            time.sleep(5)

            logging.info("Overlay cleared. Continuing...")
    except TimeoutException:
        logging.error("Timeout while waiting for overlay.")
    except StaleElementReferenceException:
        logging.warning("Stale element reference during overlay check.")
    except Exception as e:
        logging.error(f"Error handling overlay: {e}")


def get_destination_thread_url(destination_file_path, index):
    try:
        with open(destination_file_path, 'r') as destination_file:
            destination_thread_urls = [line.strip() for line in destination_file.readlines()]

        if 0 <= index < len(destination_thread_urls):
            return destination_thread_urls[index]
        else:
            logging.error("Invalid index for destination thread URL. Exiting.")
            return None

    except FileNotFoundError as e:
        logging.error(f"Error reading destination file: {e}")
        return None


# Configure drivers (chrome,gecko,etc..)



def delete_processed_urls(source_file_path, destination_file_path, source_url, destination_url):
    # Read the source file and filter out the processed URL
    with open(source_file_path, 'r') as source_file:
        source_urls = source_file.readlines()

    source_urls = [url.strip() for url in source_urls if url.strip() != source_url]

    # Write the filtered URLs back to the source file
    with open(source_file_path, 'w') as source_file:
        for url in source_urls:
            source_file.write(url + '\n')

    # Read the destination file and filter out the processed URL
    with open(destination_file_path, 'r') as destination_file:
        destination_urls = destination_file.readlines()

    destination_urls = [url.strip() for url in destination_urls if url.strip() != destination_url]

    # Write the filtered URLs back to the destination file
    with open(destination_file_path, 'w') as destination_file:
        for url in destination_urls:
            destination_file.write(url + '\n')


try:
    # Initial file paths
    source_file_path = # path to the source file that contains the Thread links (txt file)
    destination_file_path = # path to the destination file that contains the Thread links (txt file)
  

    is_destination_logged_in = False

    # Read source thread URLs from the text file
    with open(source_file_path, 'r') as source_file:
        source_thread_urls = [line.strip() for line in source_file.readlines()]

    if not source_thread_urls:
        logging.error("No source thread URLs found. Exiting.")
    else:
        # Read destination thread URLs from the text file
        with open(destination_file_path, 'r') as destination_file:
            destination_thread_urls = [line.strip() for line in destination_file.readlines()]

        # Process each source thread URL
        for source_thread_url, destination_thread_url in zip(source_thread_urls, destination_thread_urls):
            # Check if the destination thread URL is available
            if destination_thread_url:
                # Replicate and post
                replicate_and_post(driver, source_thread_url, source_username, source_password, destination_username,
                                   destination_password, destination_thread_url, is_destination_logged_in)
                # After the first iteration, set is_destination_logged_in to True
                is_destination_logged_in = True
                delete_processed_urls(source_file_path, destination_file_path, source_thread_url, destination_thread_url)
            else:
                logging.error("Failed to get the destination thread URL. Exiting.")
                break

    # Quit the driver after processing all source thread URLs
    driver.quit()

except FileNotFoundError as e:
    logging.error(f"Error reading source or destination file: {e}")

finally:
    pass
