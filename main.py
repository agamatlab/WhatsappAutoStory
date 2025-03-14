from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import os
import random
import time

# Configuration variables
NUM_PHOTOS_TO_POST = 5  # Change this value to post more or fewer photos
HEADLESS_MODE = False   # Set to True to run without browser UI

def post_whatsapp_stories(photo_directory, num_photos, headless=False):
    """
    Posts random photos from a directory to WhatsApp Web stories.
    
    Args:
        photo_directory (str): Path to the directory containing photos
        num_photos (int): Number of photos to randomly select and post
        headless (bool): Whether to run browser in headless mode
    """
    # Setup WebDriver with options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        print("Running in headless mode")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to WhatsApp Web
        driver.get('https://web.whatsapp.com/')
        
        # Wait for user to scan QR code and for WhatsApp to load
        print("Please scan the QR code to log in to WhatsApp Web")
        print("Waiting for login (up to 30 seconds)...")
        
        # Try different possible selectors for detecting a successful login
        login_successful = False
        login_selectors = [
            "//div[@id='app']//div[@data-testid='chatlist']",
            "//div[@id='side']",
            "//div[@data-testid='chat-list']",
            "//div[@data-testid='default-user']",
            "//div[@aria-label='Chat list']",
            "//span[contains(text(), 'Communities')]",
            "//span[contains(text(), 'Chats')]"
        ]
        
        login_successful = False
        for selector in login_selectors:
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                login_successful = True
                print("Successfully logged in!")
                # Give a moment for the interface to fully load
                time.sleep(3)
                break
            except:
                continue
                
        if not login_successful:
            print("Login timed out. Please try again and scan the QR code more quickly.")
            return
        
        # Get a list of all image files in the directory
        valid_extensions = ['.jpg', '.jpeg', '.png']
        try:
            all_photos = [
                os.path.join(photo_directory, file) 
                for file in os.listdir(photo_directory) 
                if os.path.isfile(os.path.join(photo_directory, file)) and 
                any(file.lower().endswith(ext) for ext in valid_extensions)
            ]
        except Exception as e:
            print(f"Error accessing directory {photo_directory}: {e}")
            return
        
        if not all_photos:
            print(f"No photos with extensions {valid_extensions} found in directory: {photo_directory}")
            return
        
        if len(all_photos) < num_photos:
            print(f"Warning: Only {len(all_photos)} photos found in directory. Using all available photos.")
            num_photos = len(all_photos)
        
        # Randomly select n photos
        selected_photos = random.sample(all_photos, num_photos)
        print(f"Selected {num_photos} random photos from {len(all_photos)} available photos.")
        
        # Try different possible selectors for accessing the status/story feature
        # Prioritized based on successful selectors from logs
        status_selectors = [
            # This selector worked in the logs
            "//button[@role='button'][@data-tab='2'][@aria-label='Status']",
            # Other alternatives
            "//button[@aria-label='Status']",
            "//button[@data-tab='2']",
            "//button[.//span[@data-icon='status']]",
            "//button[contains(@class, 'x78zum5')]",
            "//span[@data-icon='status']",
            "//button[.//span[@data-icon='status']]/..",
            "//svg[.//title='status']/..",
            "JSCLICK:document.querySelector('button[data-tab=\"2\"]')",
            "JSCLICK:document.querySelector('button[aria-label=\"Status\"]')",
            "JSCLICK:document.querySelector('span[data-icon=\"status\"]').closest('button')"
        ]
        
        print("Attempting to find and click the Status/Stories tab...")
        status_element = None
        
        for selector in status_selectors:
            try:
                # Check if this is a JavaScript selector
                if selector.startswith("JSCLICK:"):
                    js_selector = selector[8:]
                    print(f"Trying JavaScript click with: {js_selector}")
                    driver.execute_script(f"if({js_selector}) {{ {js_selector}.click(); return true; }} else {{ return false; }}")
                    time.sleep(0.5)
                    continue
                
                # Regular Selenium approach
                status_element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"Found Status element with selector: {selector}")
                status_element.click()
                print(f"Clicked the Status element")
                time.sleep(1)
                break
            except Exception as e:
                print(f"Error with selector '{selector}': {str(e)[:80]}...")
                continue
        
        # Wait for the status page to load
        time.sleep(1.5)
        
        # Try different possible selectors for the "Add Status" button (the plus button)
        # Prioritized based on successful selectors from logs
        add_status_selectors = [
            # This selector worked in the logs
            "//button[@aria-label='Add Status'][@data-tab='2']",
            # Other alternatives
            "//button[@title='Add Status']",
            "//button[.//span[@data-icon='plus']][@data-tab='2']",
            "//button[@aria-label='Add Status']",
            "//button[@data-tab='2']",
            "CSS:button[aria-label='Add Status']",
            "CSS:button[data-tab='2']",
            "JSCLICK:document.querySelector('button[aria-label=\"Add Status\"]')",
            "JSCLICK:document.querySelector('button[data-tab=\"2\"]')"
        ]
        
        posts_successful = 0
        for i, photo_path in enumerate(selected_photos, 1):
            print(f"\nPosting photo {i} of {num_photos}: {os.path.basename(photo_path)}")
            
            # Step 1: Find and click the "Add Status" plus button
            add_status_button = None
            for selector in add_status_selectors:
                try:
                    # Check if this is a JavaScript selector
                    if selector.startswith("JSCLICK:"):
                        js_selector = selector[8:]
                        print(f"Trying JavaScript click with: {js_selector}")
                        driver.execute_script(f"try {{ const el = {js_selector}; if(el) {{ el.click(); return true; }} }} catch(e) {{ console.error(e); return false; }}")
                        time.sleep(0.5)
                        add_status_button = True
                        break
                    
                    # Check if this is a CSS selector
                    elif selector.startswith("CSS:"):
                        css_selector = selector[4:]
                        print(f"Trying CSS selector: {css_selector}")
                        add_status_button = driver.find_element(By.CSS_SELECTOR, css_selector)
                        add_status_button.click()
                        print(f"Clicked element with CSS selector: {css_selector}")
                        time.sleep(1)
                        break
                    
                    # Regular Selenium approach with XPath
                    else:
                        add_status_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        add_status_button.click()
                        print(f"Found and clicked plus button with selector: {selector}")
                        time.sleep(1)
                        break
                except Exception as e:
                    print(f"Error with selector '{selector}': {str(e)[:80]}...")
                    continue
            
            if not add_status_button:
                print("Could not find the plus button. WhatsApp Web interface might have changed.")
                continue
                
            # Step 2: Now look for and click the "Photos & videos" button
            print("Looking for 'Photos & videos' button...")
            # Prioritized based on successful selectors from logs
            photos_videos_selectors = [
                # This selector worked in the logs
                "//span[@data-icon='media-multiple']/parent::div",
                # Other alternatives
                "//div[.//span[@data-icon='media-multiple']]",
                "//span[text()='Photos & videos']/parent::div",
                "//div[contains(@class, 'x1c4vz4f')][.//span[@data-icon='media-multiple']]",
                "CSS:div:has(span[data-icon='media-multiple'])",
                "CSS:span.x1o2sk6j:contains('Photos & videos')",
                "JSCLICK:document.querySelector('span[data-icon=\"media-multiple\"]').closest('div')",
                "JSCLICK:Array.from(document.querySelectorAll('span')).find(el => el.textContent.includes('Photos & videos')).closest('div')"
            ]
            
            photos_videos_clicked = False
            for selector in photos_videos_selectors:
                try:
                    # Check if this is a JavaScript selector
                    if selector.startswith("JSCLICK:"):
                        js_selector = selector[8:]
                        print(f"Trying JavaScript click with: {js_selector}")
                        driver.execute_script(f"try {{ const el = {js_selector}; if(el) {{ el.click(); return true; }} }} catch(e) {{ console.error(e); return false; }}")
                        time.sleep(1)
                        photos_videos_clicked = True
                        break
                    
                    # Check if this is a CSS selector
                    elif selector.startswith("CSS:"):
                        css_selector = selector[4:]
                        print(f"Trying CSS selector: {css_selector}")
                        photos_button = driver.find_element(By.CSS_SELECTOR, css_selector)
                        photos_button.click()
                        print(f"Clicked 'Photos & videos' with CSS selector: {css_selector}")
                        time.sleep(1)
                        photos_videos_clicked = True
                        break
                    
                    # Regular Selenium approach with XPath
                    else:
                        photos_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        photos_button.click()
                        print(f"Found and clicked 'Photos & videos' with selector: {selector}")
                        time.sleep(1)
                        photos_videos_clicked = True
                        break
                except Exception as e:
                    print(f"Error with 'Photos & videos' selector '{selector}': {str(e)[:80]}...")
                    continue
            
            if not photos_videos_clicked:
                print("Could not find the 'Photos & videos' button after clicking plus. Trying to proceed anyway...")
            
            # Step 3: Handle file upload
            try:
                # First try standard file input approach - prioritized from logs
                file_input = None
                input_selectors = [
                    # This selector worked in the logs
                    "//input[@type='file']",
                    # Other alternatives
                    "//input[contains(@accept, 'image')]",
                    "//input[contains(@type, 'file')]",
                    "CSS:input[type='file']"
                ]
                
                for selector in input_selectors:
                    try:
                        print(f"Looking for file input with selector: {selector}")
                        if selector.startswith("CSS:"):
                            file_input = driver.find_element(By.CSS_SELECTOR, selector[4:])
                        else:
                            file_input = driver.find_element(By.XPATH, selector)
                            
                        if file_input:
                            print(f"Found file input with selector: {selector}")
                            break
                    except Exception as e:
                        print(f"No file input found with selector {selector}")
                        
                # If no file input found, try injection approach
                if not file_input:
                    print("No standard file input found. Creating a hidden file input...")
                    
                    # Create a hidden file input element
                    input_id = driver.execute_script("""
                        // Create a file input
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = 'image/*';
                        input.style.display = 'none';
                        input.id = 'whatsapp-file-input';
                        document.body.appendChild(input);
                        return input.id;
                    """)
                    
                    file_input = driver.find_element(By.ID, input_id)
                    
                # Input the file path (use absolute path)
                abs_path = os.path.abspath(photo_path)
                print(f"Sending file path to input: {abs_path}")
                file_input.send_keys(abs_path)
                print("File path sent successfully")
                
                # Wait for the upload to process
                time.sleep(1)
                
                # Try to find the send button - prioritized from logs
                send_selectors = [
                    # This selector worked in the logs
                    "//div[contains(@aria-label, 'Send')]",
                    # Other alternatives
                    "//div[@data-testid='send']", 
                    "//span[contains(text(), 'Send')]//ancestor::div[@role='button']",
                    "//button[contains(@aria-label, 'Send')]",
                    "//div[@role='button'][contains(@class, 'send')]",
                    "//div[@role='button'][.//span[@data-icon='send']]",
                    "CSS:div[data-testid='send']",
                    "CSS:div[role='button']:has(span[data-icon='send'])"
                ]
                
                send_button = None
                for selector in send_selectors:
                    try:
                        if selector.startswith("CSS:"):
                            send_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector[4:]))
                            )
                        else:
                            send_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        print(f"Found send button with selector: {selector}")
                        send_button.click()
                        print("Clicked send button")
                        posts_successful += 1
                        break
                    except Exception as e:
                        print(f"Error with send button selector '{selector}': {str(e)[:80]}...")
                        continue
                
                if not send_button:
                    print("Could not find the 'Send' button. WhatsApp Web interface might have changed.")
                
                # Wait before proceeding to the next photo
                time.sleep(1.5)
                
            except Exception as e:
                print(f"Error uploading photo {photo_path}: {e}")
                continue
        
        if posts_successful > 0:
            print(f"\nSuccessfully posted {posts_successful} out of {num_photos} photos to WhatsApp stories!")
        else:
            print("\nFailed to post any photos. WhatsApp Web interface might have changed or there might be issues with the upload process.")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    finally:
        # Ask if user wants to keep the browser open
        if not headless:
            try:
                keep_open = input("Do you want to keep the browser open? (y/n): ")
                if keep_open.lower() != 'y':
                    driver.quit()
                    print("Browser closed.")
                else:
                    print("Browser remains open. Please close it manually when done.")
            except KeyboardInterrupt:
                print("\nProgram interrupted. Closing browser.")
                driver.quit()
            except Exception as e:
                print(f"\nError during browser closure prompt: {e}")
                driver.quit()
                print("Browser closed due to error.")
        else:
            driver.quit()
            print("Headless browser closed.")

if __name__ == "__main__":
    # Determine the path to the "pictures" folder in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pictures_dir = os.path.join(script_dir, "pictures")
    
    # Validate inputs
    if not os.path.isdir(pictures_dir):
        print(f"Error: Pictures directory '{pictures_dir}' does not exist.")
        print(f"Please create a folder named 'pictures' in {script_dir} and add your photos to it.")
    elif NUM_PHOTOS_TO_POST <= 0:
        print("Error: NUM_PHOTOS_TO_POST must be greater than 0.")
        print("Please edit the script and set NUM_PHOTOS_TO_POST to a positive number.")
    else:
        print(f"Starting WhatsApp Story Poster")
        print(f"Using pictures from: {pictures_dir}")
        print(f"Number of photos to post: {NUM_PHOTOS_TO_POST}")
        
        post_whatsapp_stories(pictures_dir, NUM_PHOTOS_TO_POST, HEADLESS_MODE)