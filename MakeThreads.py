import logging
import re
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

MAX_LOGIN_ATTEMPTS = 3

# Source and destination credentials
source_username = #source username
source_password = #source password
destination_username = #destination username
destination_password = #destinationa password

destination_success_url = # Assign a destination url, it'll be the url after you login in to the forum
destination_login_url = # Login url to the destination forum here

source_success_url = # Assign a source url, it'll be the url after you login in to the forum
source_login_url = # Login url to the source forum here



def save_unsuccessful_name(thread_name):
    try:
        unsuccessful_names_file_path = # path to a file that will store unsuccessful names 
        with open(unsuccessful_names_file_path, 'a', encoding='utf-8') as file:
            file.write(f"{thread_name}\n")
        print("Unsuccessful name saved to file.")
    except Exception as e:
        print(f"Error saving unsuccessful name: {e}")


def save_unsuccessful_link(destination_node_url):
    try:
        print(f"Attempting to save unsuccessful link: {destination_node_url}")
        unsuccessful_links_file_path = # path to a file that will store unsuccessful links
        with open(unsuccessful_links_file_path, 'a', encoding='utf-8') as file:
            file.write(f"{destination_node_url}\n")
        print("Unsuccessful link saved to file.")
    except Exception as e:
        print(f"Error saving unsuccessful link: {e}")


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

            password_field.send_keys(Keys.RETURN)  # Sending Enter key instead of using submit()

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
            logging.error("Exception details:", exc_info=True)  # This line will print exception details

            if attempt <= MAX_LOGIN_ATTEMPTS:
                attempt += 1
            else:
                logging.error("Max login attempts reached. Exiting.")
                return False

    logging.error("Failed to login after {} attempts. Exiting.".format(MAX_LOGIN_ATTEMPTS))
    return False


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


def save_created_threads(thread_name, created_thread_url):
    try:
        created_threads_file_path = # file path to newly created Thread links
        with open(created_threads_file_path, 'a', encoding='utf-8') as file:
            file.write(f"{created_thread_url}\n")
        print("Created thread saved to file.")
    except Exception as e:
        print(f"Error saving created thread: {e}")


def save_used_source_links(source_name, source_link):
    try:
        used_source_links_file_path = # file path to used source Thread links
        with open(used_source_links_file_path, 'a', encoding='utf-8') as file:
            file.write(f"{source_link}\n")
        print("Used source link saved to file.")
    except Exception as e:
        print(f"Error saving used source link: {e}")


def scrape_post_information(driver, source_thread_url, source_username, source_password, login_required=False):
    global post_index
    post_info_list = []

    def extract_text_content(bb_wrapper_element):
        try:
            # Exclude link elements and elements with class bbCodeSpoiler-button-title from the text content
            text_content = bb_wrapper_element.text
            links = bb_wrapper_element.find_elements(By.XPATH, ".//a[@href]")
            spoilers = bb_wrapper_element.find_elements(By.CLASS_NAME, "bbCodeSpoiler-button-title")

           
            text_content = # Hard-coded removal of desired links from being scrapped

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

    driver.get(source_thread_url)
    logging.info(f"Opened post page: {source_thread_url}")

    try:
        bb_wrapper_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH,
                                                 "//article[contains(@class,'message')]//div[contains(@class,"
                                                 "'message-userContent')]//div[contains(@class,'bbWrapper')]"))
        )
        logging.info(f"Number of bb_wrapper_elements: {len(bb_wrapper_elements)}")

        for post_index, bb_wrapper_element in enumerate(bb_wrapper_elements[:1], start=1):
            logging.info(f"Processing post {post_index}")
            text_content = extract_text_content(bb_wrapper_element)

            contains_only_blacklisted = all(
                blacklisted_sentence in text_content for blacklisted_sentence in blacklist)

            if contains_only_blacklisted:
                logging.info(f"Skipping post {post_index} as it contains only blacklisted sentence(s).")
                continue

            # Remove blacklisted sentences
            for blacklisted_sentence in blacklist:
                text_content = re.sub(r'\b{}\b'.format(re.escape(blacklisted_sentence)), '', text_content,
                                      flags=re.IGNORECASE)

            # Remove empty lines after removing blacklisted sentences
            text_content = '\n'.join([sentence for sentence in text_content.split('\n') if sentence.strip()])

            # Remove any duplicate empty lines
            text_content = re.sub(r'\n{2,}', '\n', text_content)

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
        logging.error(f"Error extracting information: {e}")

    except TimeoutException:
        logging.error("Timeout while scraping post information")

    logging.info(f"Number of posts scraped: {len(post_info_list)}")
    return post_info_list


def clean_string(input_string):
    cleaned_string = input_string.strip().lower()
    return cleaned_string


def create_and_post_destination_thread(driver, destination_node_url, thread_name, source_name, source_link,
                                       scraped_post_info):
    try:
        print(f"Attempting to create and post thread at: {destination_node_url}")

        if destination_node_url is None:
            print("No matching node found. Skipping thread creation.")
            return False  # Return False indicating thread creation failed

        # Open the destination node URL
        driver.get(destination_node_url)

        title_input_locator = (By.CLASS_NAME, "input--title")
        title_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(title_input_locator)
        )

        print(f"Located title input: {title_input.get_attribute('outerHTML')}")
        title_input.clear()
        title_input.send_keys(thread_name)

        # Use WebDriverWait for the message box
        message_box_locator = (By.CLASS_NAME, "fr-element-scroll-visible")
        message_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(message_box_locator)
        )
        message_box.clear()

        for post_info in scraped_post_info:
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

            # Append the content to the message box
            message_box.send_keys(content)

            # Add a new line to separate posts
            message_box.send_keys(Keys.RETURN)

        # Use WebDriverWait for the post button
        post_button_locator = (By.CLASS_NAME, "button--icon--write")
        post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(post_button_locator)
        )
        post_button.click()

        # Add a delay of 2 seconds after clicking the "Post" button
        time.sleep(10)

        # Wait for the URL to change (indicating the new thread is created)
        WebDriverWait(driver, 10).until(lambda d: d.current_url != destination_node_url)

        # Get the URL of the created thread
        created_thread_url = driver.current_url
        print(f"Thread '{thread_name}' successfully created and posted. Thread URL: {created_thread_url}")
        save_created_threads(thread_name, created_thread_url)
        save_used_source_links(source_name, source_link)

        # Thread creation and posting successful
        return True

    except WebDriverException as e:
        # Treat the BMP error
        print(f"Error creating and posting thread: {e}")
        save_unsuccessful_link(destination_node_url)
        save_unsuccessful_name(thread_name)
        return False

    except Exception as e:
        # Other exceptions

        print(f"Error creating and posting thread: {e}")
        save_unsuccessful_link(destination_node_url)
        save_unsuccessful_name(thread_name)
        return False  # Return False indicating thread creation failed


def is_logged_in(driver):
    try:
        login_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='blockMessage' and contains(text(), 'You are "
                                                      "already logged in.')]"))
        )
        return login_element is not None
    except TimeoutException:
        return False


def main():
    source_thread_names_file = # file to the names of the Threads 
    destination_thread_names_file = # file to the archived names to avoid duplicates
    source_thread_links_file = # file to the source links 

    destination_node_links = [
        # destination node urls ( where the threads will be made)
    ]

    NODE_ATTEMPT_THRESHOLD = 200000  # adjust value 

    success_counts = [0] * len(destination_node_links)
    total_counts = [0] * len(destination_node_links)

#CONFIGURE DRIVER

    try:
        with open(source_thread_names_file, 'r', encoding='utf-8') as f_source_names, \
                open(destination_thread_names_file, 'r', encoding='utf-8') as f_dest_names, \
                open(source_thread_links_file, 'r', encoding='utf-8') as f_source_links:

            source_names = f_source_names.read().splitlines()
            dest_names = f_dest_names.read().splitlines()
            source_links = f_source_links.read().splitlines()

            current_node_index = 0
            links_assigned = 0

            for source_name, source_link in zip(source_names, source_links):
                if source_name not in dest_names:
                    post_info_list = scrape_post_information(driver, source_link, source_username, source_password,
                                                             False)
                    if post_info_list:
                        if not is_logged_in(driver):
                            login(driver, destination_username, destination_password, destination_login_url,
                                  destination_success_url)

                        if create_and_post_destination_thread(
                                driver, destination_node_links[current_node_index], thread_name=source_name,
                                source_name=source_name, source_link=source_link,
                                scraped_post_info=post_info_list
                        ):
                            success_counts[current_node_index] += 1
                            total_counts[current_node_index] += 1
                        else:
                            total_counts[current_node_index] += 1

                        links_assigned += 1

                        if current_node_index >= len(destination_node_links):
                            continue

                        if links_assigned >= 200000:
                            current_node_index += 1
                            links_assigned = 0
                            continue

                        if total_counts[current_node_index] >= NODE_ATTEMPT_THRESHOLD:
                            current_node_index += 1
                            links_assigned = 0
                            continue

                    print(f"Total counts for current node: {total_counts[current_node_index]}")
                    print(f"Success counts for current node: {success_counts[current_node_index]}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
