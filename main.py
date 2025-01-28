import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from twocaptcha import TwoCaptcha
from utils.actions import PageActions
from utils.helpers import CaptchaHelper
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.text import MIMEText
from selenium.webdriver.chrome.options import Options
import sys
import pytz

# CONFIGURATION
url = "https://relyhome.com/login/"
apikey = 'd256a1ca7a8d707de6f83e40a374a3c1'  # 2Captcha API key
solver = TwoCaptcha(apikey, pollingInterval=1)

# LOCATORS
c_try_again = "//div[@class='rc-imageselect-incorrect-response']"
c_select_more = "//div[@class='rc-imageselect-error-select-more']"
c_dynamic_more = "//div[@class='rc-imageselect-error-dynamic-more']"
c_select_something = "//div[@class='rc-imageselect-error-select-something']"
c_iframe_captcha = "//iframe[@title='reCAPTCHA']"
c_checkbox_captcha = "//span[@role='checkbox']"
c_popup_captcha = "//iframe[contains(@title, 'two minutes')]"
c_verify_button = "//button[@id='recaptcha-verify-button']"
signin_button = "//button[@type='submit']"
jobs_available_xpath = "//*[@id='sidebar']/div[2]/div[1]/div[2]/div/div/div/div/ul/li[13]/a"
 
# Define the log file


# Counter for the submissions
submission_count = 0
 
email_sent = False
last_available_jobs_count = 0 

est_timezone = pytz.timezone("US/Eastern")


def send_email_notification(subject, body):
    from_email = "botautomation707@gmail.com"  # Replace with your email
    from_name = "Bot"  # Desired sender name
    to_email = ["samuelcabagay707@gmail.com","jmarcelino@fidelisrepairs.com"]   # Replace with your email or desired recipient
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>" 
    msg["To"] = ", ".join(to_email)

    # Using Gmail's SMTP server with SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("botautomation707@gmail.com", "lnrwjzugoanukyhd")  # Use app password here
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent")


def send_email_notification_to_me(subject, body):
    from_email = "botautomation707@gmail.com"  # Replace with your email
    from_name = "Bot"  # Desired sender name
    to_email = ["samuelcabagay707@gmail.com"]   # Replace with your email or desired recipient
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>" 
    msg["To"] = ", ".join(to_email)

    # Using Gmail's SMTP server with SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("botautomation707@gmail.com", "lnrwjzugoanukyhd")  # Use app password here
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent")

# MAIN TASK: Login and click button based on location filter
def login_and_click_button():
    global submission_count
    global last_available_jobs_count    # Access the global submission count

    options = Options()
    options.add_argument("--headless")  # Enables headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
    options.add_argument("--no-sandbox")  # Disable sandboxing (optional)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Explicitly set the window size
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})

    with webdriver.Chrome(options=options) as browser:
        browser.maximize_window()
        start_time = time.time()  
        while True:
            try:
                if time.time() - start_time >= 3000:  # 1200 seconds = 20 minutes
                    print(f"Restarting program after 50 minutes.")
                    start_time = time.time()  


                browser.get(url)
                print("Started")

                # Instantiate helper classes
                page_actions = PageActions(browser)
                page_actions.enter_credentials("FL-NorthWest@FidelisRepairs.com", "Fidelis1!")
                captcha_helper = CaptchaHelper(browser, solver)

                # Click on the captcha checkbox
                page_actions.switch_to_iframe(c_iframe_captcha)
                page_actions.click_checkbox(c_checkbox_captcha)
                page_actions.switch_to_default_content()
                page_actions.switch_to_iframe(c_popup_captcha)
                time.sleep(1)

                script_get_data_captcha = captcha_helper.load_js_script('js_scripts/get_captcha_data.js')
                script_change_tracking = captcha_helper.load_js_script('js_scripts/track_image_updates.js')

                captcha_helper.execute_js(script_get_data_captcha)
                captcha_helper.execute_js(script_change_tracking)

                id = None  

                while True:
                    captcha_data = browser.execute_script("return getCaptchaData();")
            
                    params = {
                        "method": "base64",
                        "img_type": "recaptcha",
                        "recaptcha": 1,
                        "cols": captcha_data['columns'],
                        "rows": captcha_data['rows'],
                        "textinstructions": captcha_data['comment'],
                        "lang": "en",
                        "can_no_answer": 1
                    }
            
                    if params['cols'] == 3 and id:
                        params["previousID"] = id
            
                    print("Params before solving captcha:", params)
            
                    result = captcha_helper.solver_captcha(file=captcha_data['body'], **params)
            
                    if result is None:
                        print("Captcha solving failed or timed out. Stopping the process.")
                        break
            
                    elif result and 'No_matching_images' not in result['code']:
                        if id is None and params['cols'] == 3 and result['captchaId']:
                            id = result['captchaId']  # Save id for subsequent iterations
            
                        answer = result['code']
                        number_list = captcha_helper.pars_answer(answer)
            
                        # Processing for 3x3
                        if params['cols'] == 3:
                            page_actions.clicks(number_list)
            
                            image_update = page_actions.check_for_image_updates()
            
                            if image_update:
                                print(f"Images updated, continuing with previousID: {id}")
                                continue  
            
                            page_actions.click_check_button(c_verify_button)
            
                        # Processing for 4x4
                        elif params['cols'] == 4:
                            page_actions.clicks(number_list)
                            page_actions.click_check_button(c_verify_button)
            
                            image_update = page_actions.check_for_image_updates()
            
                            if image_update:
                                print(f"Images updated, continuing without previousID")
                                continue  
            
                        # If the images are not updated, check the error messages
                        if captcha_helper.handle_error_messages(c_try_again, c_select_more, c_dynamic_more, c_select_something):
                            continue  
            
                        # If there are no errors, send the captcha
                        page_actions.switch_to_default_content()
                        page_actions.click_check_button(signin_button)
                        break  
            
                    elif 'No_matching_images' in result['code']:
                        # If the captcha returned the code "no_matching_images", check the errors
                        page_actions.click_check_button(c_verify_button)
                        if captcha_helper.handle_error_messages(c_try_again, c_select_more, c_dynamic_more, c_select_something):
                            continue  
                        else:
                            page_actions.switch_to_default_content()
                            page_actions.click_check_button(signin_button)
                            break  

                # Check if login was successful by verifying URL or page content
                current_url = browser.current_url
                if "jobs/available" in browser.current_url:
                    print("Login successful. Redirected to available jobs page.")
                    try:
                        close_button = WebDriverWait(browser, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@class='close-btn']"))
                        )
                        close_button.click()
                        print("Close button clicked.")
                    except Exception as e:
                        print(f"Error while clicking close button: {e}")
                    while True:
                        try:
                            print("Waiting for available jobs...", browser.current_url)
                            # Locate all rows in the data table
                            rows = WebDriverWait(browser, 15).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[@id='DataTables_Table_0']/tbody/tr"))
                            )
                            if "No data available in table" in browser.page_source:
                                print("No available jobs at the moment.")
                            else:
                                available_jobs_count = len(rows)
                                print(f"Available jobs count: {available_jobs_count}")
                                current_time_est = datetime.now(est_timezone).strftime('%Y-%m-%d %H:%M:%S')
                                table = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//table")))
                                headers = table.find_elements(By.XPATH, ".//thead/tr/th")
                                header_map = {header.text.strip().lower(): index + 1 for index, header in enumerate(headers)}
                                for row in rows:
                                    try:
                                        system = row.find_element(By.XPATH, f".//td[{header_map['system']}]").text
                                        brand = row.find_element(By.XPATH, f".//td[{header_map['brand']}]").text
                                        location = row.find_element(By.XPATH, f".//td[{header_map['location']}]").text
                                        distance = row.find_element(By.XPATH, f".//td[{header_map['distance']}]").text
                                        company = row.find_element(By.XPATH, f".//td[{header_map['company']}]").text
                                
                                        send_email_notification_to_me(
                                            "Available Jobs", 
                                             f"System: {system}, Brand: {brand}, Location: {location}, Distance: {distance}, Company: {company}\n\n"
                                             f"TimeStamp: {current_time_est}"

                                        )
                                    except Exception as e:
                                        print(f"Error processing row: {e}")
                                        continue
                                if available_jobs_count != last_available_jobs_count:
                                    if browser.current_url == "https://relyhome.com/tasks/":
                                        send_email_notification(
                                            "Task Notification", 
                                            f"Total Task: {available_jobs_count} \n\n" 
                                            "The Bot is currently on the Tasks page. Please visit the website to complete the tasks before the bot can proceed to the Jobs Available page. \n\n"
                                            "[Email account: FL-NorthWest@FidelisRepairs.com] You can log in here: https://relyhome.com/login/\n\n"
                                            "After completing the tasks, please contact the developer to run the bot again."

                                        )                                   
                                        last_available_jobs_count = available_jobs_count
                                        email_sent = True
                                        sys.exit()

                            button_clicked = False

                            # Iterate through each row to check location
                            for row in rows:
                                try:
                                    table = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//table")))
                                    headers = table.find_elements(By.XPATH, ".//thead/tr/th")
                                    header_map = {header.text.strip().lower(): index + 1 for index, header in enumerate(headers)}

                                    swo_td = row.find_element(By.XPATH, f".//td[{header_map.get('swo #', 1)}]")
                                    swo_number = swo_td.text.strip()
                                    # Get the 3rd <td> element (location)
                                    location_td = row.find_element(By.XPATH, f".//td[{header_map['location']}]")
                                    location_text = location_td.text.strip()

                                    # Get the 2nd <td> element (system)
                                    system_td = row.find_element(By.XPATH, f".//td[{header_map['system']}]")
                                    system_text = system_td.text.strip()
                            
                                    # Skip rows where the system contains "Septic"
                                    if "septic" in system_text.lower() or "service line" in system_text.lower():
                                        print(f"Skipping job with system: {system_text}")
                                        continue

                                    # Check if location contains "Florida", "FL", "fl"
                                    if any(loc in location_text.lower() for loc in ["florida", "fl"]):
                                        print(f"Matching location found: {location_text} (SWO# {swo_number})")
                                        
                                        # Click the button in the same row
                                        button = row.find_element(By.XPATH, f".//td[{header_map['actions']}]//a[contains(@class, 'btn-primary')]")
                                        button.click()
                                        print("Button clicked for:", location_text)
                                        button_clicked = True
                                        break  # Stop after first match

                                except Exception as e:
                                    print("Error processing row")

                                    continue



                            def add_day_suffix(day):
                                if 10 <= day <= 20:  # Special case for 11th, 12th, 13th
                                    suffix = 'th'
                                else:
                                    suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                                return f"{day}{suffix}"

                            
                            
                            today = datetime.now(est_timezone)
                            desired_day = today + timedelta(days=2)  # This will select the day 2 days from today (e.g., Monday -> Wednesday)
                            
                            
                            if today.weekday() == 4:  # Friday
                                desired_day = today + timedelta(days=3)  # Skip to Monday
                            
                            elif today.weekday() == 3:  # Thursday
                                desired_day = today + timedelta(days=4)  # Skip to Monday

                                # Check if today is a weekend (Saturday or Sunday)
                            elif today.weekday() == 5:  # Saturday
                                # Set desired day to Monday if today is Saturday
                                desired_day = today + timedelta(days=2)
                            elif today.weekday() == 6:  # Sunday
                                # Set desired day to Tuesday if today is Sunday
                                desired_day = today + timedelta(days=2)
                            
                            desired_day_name = desired_day.strftime('%A')  # Get the weekday name (e.g., "Monday")
                            desired_day_date = desired_day.strftime('%d %B, %Y')

                            day_number = int(desired_day.strftime('%d'))
                            
                            desired_day_with_weekday = f"{desired_day_name} {desired_day.strftime('%B')} {add_day_suffix(day_number)}, {desired_day.strftime('%Y')}"
                            desired_day_date_normalized = f"{add_day_suffix(day_number)} {desired_day.strftime('%B, %Y')}"
                            
                            if button_clicked:
                                try:
                                    close_button = WebDriverWait(browser, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, "//button[@class='close-btn']"))
                                    )
                                    close_button.click()
                                    print("Close button clicked.")
                                except Exception as e:
                                    print("Button not available")

                                # Process radio buttons and submit the form

                                li_elements = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@id='frm']/div[2]//li")))
                                for li in li_elements:
                                    try:
                                        # Scroll to the SYSTEM element and get its text
                                        system_element = li.find_element(By.XPATH, "//*[@id='swo-accept-box']/div[1]")
                                        browser.execute_script("arguments[0].scrollIntoView(true);", system_element)  # Scroll to the SYSTEM element
                                        system_text = system_element.text.replace("SYSTEM:", "").strip()

                                        
                                        # Scroll to the LOCATION element and get its text
                                        location_element = li.find_element(By.XPATH, "//*[@id='swo-accept-box']/div[2]")
                                        browser.execute_script("arguments[0].scrollIntoView(true);", location_element)  # Scroll to the LOCATION element
                                        location_text = location_element.text.replace("LOCATION:", "").strip()

                                        day_text = li.find_element(By.XPATH, ".//strong").text.strip()
                                        print(f"Day text: {day_text}, Desired day with weekday: {desired_day_with_weekday}, Desired day date: {desired_day_date_normalized}")
                                        if desired_day_with_weekday == day_text:
                                            print(f"Selecting {day_text}...")

                                            # Find specific time slots and click the first available slot
                                            time_slots = li.find_elements(By.NAME, "appttime")
                                            for slot in time_slots:
                                                slot_text = slot.find_element(By.XPATH, "..").text.strip()
                                                if "11:00 AM - 03:00 PM" in slot_text:
                                                    print("Selecting 11:00 AM - 03:00 PM time slot.")
                                                    browser.execute_script("arguments[0].scrollIntoView(true);", slot)
                                                    slot.click()
                                                    break
                                                elif "07:00 AM - 11:00 AM" in slot.get_attribute("outerHTML"):
                                                    print("Selecting 07:00 AM - 11:00 AM slot.")
                                                    browser.execute_script("arguments[0].scrollIntoView(true);", slot)
                                                    slot.click()
                                                    break
                                                elif "03:00 PM - 08:00 PM" in slot.get_attribute("outerHTML"):
                                                    print("Selecting 03:00 PM - 08:00 PM slot.")
                                                    browser.execute_script("arguments[0].scrollIntoView(true);", slot)
                                                    slot.click()
                                                    break

                                            # Submit the form
                                            submit_button = WebDriverWait(browser, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
                                            )
                                            browser.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                                            time.sleep(1)  # Wait for the scroll to complete
                                            print("Submitting selection...")
                                            submit_button.click()
                                            # Increment the submission count
                                            submission_count += 1
                                            print(f"Total submissions: {submission_count}")
                                            
                                            # Log the submission
                                            current_time_est = datetime.now(est_timezone).strftime('%Y-%m-%d %H:%M:%S')

                                            send_email_notification(
                                                "Job Accepted Notification",
                                                f"Job has been successfully accepted - {current_time_est}\n\n"
                                                f"SYSTEM: {system_text}\n"
                                                f"LOCATION: {location_text}\n"
                                                f"DAY: {day_text}\n"
                                                f"TIME: {slot_text}\n"
                                                f"URL: {browser.current_url}\n\n"
                                                "Visit the website for more information or to reschedule the day.\n"
                                                "[Email account: FL-NorthWest@FidelisRepairs.com]"
                                            )


                                            # Return to jobs/available page
                                            print("Returning to jobs/available...")
                                            browser.get("https://relyhome.com/jobs/available/")
                                            break  # Return to job search loop
                                        else:
                                            print(f"Skipping {day_text} as it is not the desired day ({desired_day_name}).")

                                    except Exception as e:
                                        print(f"Error processing radio buttons: {e}")
                                        continue

                            else:
                                print("No matching jobs found. Retrying...", browser.current_url)
                                # Click the 'jobs_available_xpath' to reload the job listings page
                                jobs_available_link = WebDriverWait(browser, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, jobs_available_xpath)))
                                jobs_available_link.click()
                                time.sleep(3)

                        except Exception as e:
                            print(f"No jobs available or error: {e}. Retrying...", browser.current_url) 
                            # Click the 'jobs_available_xpath' to reload the job listings page
                            jobs_available_link = WebDriverWait(browser, 10).until(
                                EC.element_to_be_clickable((By.XPATH, jobs_available_xpath))
                            )
                            jobs_available_link.click()
                            time.sleep(3)

                else:
                    print("Login failed. Current URL:", browser.current_url)
                    # Check if the current URL is the tasks page
                    if browser.current_url == "https://relyhome.com/tasks/" and not hasattr(browser, 'email_sent'):
                        send_email_notification(
                            "Task Notification", 
                            "The Bot is currently on the Tasks page. Please visit the website to complete the tasks before the bot can proceed to the Jobs Available page. \n\n"
                            "[Email account: FL-NorthWest@FidelisRepairs.com] You can log in here: https://relyhome.com/login/\n\n"
                            "After completing the tasks, please contact the developer to run the bot again."
                        )
                        # Set an attribute to flag that the email has been sent
                        browser.email_sent = True

                    if browser.current_url == "https://relyhome.com/tasks/":
                        # If the email has already been sent, log out again
                        my_account_button = browser.find_element(By.ID, "page-header-user-dropdown")
                        my_account_button.click()
                        logout_button = browser.find_element(By.XPATH, "//a[@href='https://relyhome.com/logout/']")
                        logout_button.click()
                        sys.exit()

                        

                    time.sleep(5)
                    continue

            except Exception as e:
                print(f"Unexpected error: {e}. Restarting process...")
                if browser.current_url == "https://relyhome.com/dashboard/":
                    # If the email has already been sent, log out again
                    my_account_button = browser.find_element(By.ID, "page-header-user-dropdown")
                    my_account_button.click()
                    logout_button = browser.find_element(By.XPATH, "//a[@href='https://relyhome.com/logout/']")
                    logout_button.click()
                time.sleep(10)
                continue

if __name__ == "__main__":
    login_and_click_button()
