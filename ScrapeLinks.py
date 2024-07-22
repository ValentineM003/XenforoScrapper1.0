import logging
import random
import string
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO)


def write_ascii_only(file, text):
    ascii_text = ''.join(char for char in text if ord(char) < 128)
    file.write(ascii_text + '\n')


def get_number_of_pages(driver, thread_url):
    driver.get(thread_url)
    try:
        pagination = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pageNav-main"))
        )
        page_links = pagination.find_elements(By.CLASS_NAME, "pageNav-page")
        page_numbers = [int(link.text) for link in page_links if link.text.isdigit()]
        max_page_number = max(page_numbers) if page_numbers else 1
        return max_page_number
    except TimeoutException:
        logging.error("Timeout while analyzing thread pages. Assuming only one page.")
        return 1


def scrape_threads_on_page(driver, threads_file, names_file, existing_thread_names, max_range, current_node_url):
    total_thread_counter = 0
    visited_pages = set()  # Keep track of visited pages to avoid revisiting

    while total_thread_counter < 100000 and len(visited_pages) < max_range:  # adjust range 
        random_page = random.randint(1, max_range)
        if random_page not in visited_pages:
            visited_pages.add(random_page)
        else:
            random_page += 1  # Increment random page number if already visited

        page_url = current_node_url.rstrip('/') + f'/page-{random_page}'  # Form the page URL
        print(f"Scraping page: {random_page}")  # Print the current page being scraped
        try:
            driver.get(page_url)
            remaining_threads = 100000  - total_thread_counter  # adjust value
            print(f"Already scraped {total_thread_counter} threads, need to scrape {remaining_threads} more.")
            thread_counter = scrape_single_page(driver, threads_file, names_file,
                                                existing_thread_names, remaining_threads)
            total_thread_counter += thread_counter

            # If total threads scraped exceeds desired value, break the loop
            if total_thread_counter >= 100000:  # adjust value 
                break

            # If the current page doesn't have enough unique threads, generate a new URL
            if thread_counter == 0:
                print("No new threads found on this page. Generating a new URL...")
                continue

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Cleaning URL box...")
            driver.execute_script("window.location.href = ''")  # Clear URL box

    print(f"Total {total_thread_counter} thread links and names scraped.")

max_threads = # number of threads to be scrapped

def scrape_single_page(driver, threads_file, names_file, existing_thread_names, max_threads):
    thread_counter = 0

    thread_links = driver.find_elements(By.CSS_SELECTOR, ".structItem-title a")
    for link in thread_links:
        if thread_counter >= max_threads:
            break  # Exit loop if we've collected enough threads
        thread_name = link.text.strip()
        thread_href = link.get_attribute("href")
        if "forums/" not in thread_href and "members/" not in thread_href:
            if thread_name not in existing_thread_names:
                threads_file.write(f"{thread_href}\n")
                write_ascii_only(names_file, thread_name)  # Save thread name to file
                logging.info(f"Thread Name: {thread_name}, URL: {thread_href}")
                existing_thread_names.add(thread_name)
                thread_counter += 1
            else:
                logging.info(f"Skipping thread {thread_name}, already exists")

    return thread_counter


def write_to_file(file, data):
    try:
        file.write(data + '\n')
    except Exception as e:
        logging.error(f"Error occurred while writing to file: {e}")


def clean_desarchive_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            cleaned_line = ''.join(char for char in line if char in string.printable)
            file.write(cleaned_line)


def scrape_threads_with_edge(source_nodes):

# CONFIGURE DRIVER

    desarchive_file_path = # file path to a txt file that contains all the thread names so the code doesn't scrape duplicates 
    clean_desarchive_file(desarchive_file_path)

    threads_file_path = # destination file path where links will be stored
    names_file_path = # file which the thread names will be stored

    try:
        with open(threads_file_path, 'w', encoding='utf-8') as threads_file, \
                open(names_file_path, 'w', encoding='utf-8') as names_file, \
                open(node_history_file_path, 'w', encoding='utf-8') as node_history_file, \
                open(desarchive_file_path, 'r', encoding='utf-8') as desarchive_file:

            existing_thread_names = set(line.strip() for line in desarchive_file)

            for source_node in source_nodes:
                logging.info(f"Scraping from: {source_node}")

                node_name = source_node.split('/')[-2].split('.')[0]

                for _ in range(100000): # adjust range 
                    write_ascii_only(node_history_file, node_name)

                driver.get(source_node)

                max_range = get_number_of_pages(driver, source_node)
                time.sleep(5)
                # Pass file objects instead of file paths
                scrape_threads_on_page(driver, threads_file, names_file, existing_thread_names, max_range, source_node)

                # Wait for 6 seconds after scraping each node
                time.sleep(20)

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
    finally:
        driver.quit()


source_nodes = [
    # list of forum node urls that the code should scrape threads from
]
scrape_threads_with_edge(source_nodes)
