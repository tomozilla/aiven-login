from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import os
import time
import argparse
import json

# Load environment variables
load_dotenv()

def init_driver():
    """Initialize Selenium WebDriver with headless options for Ubuntu server"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")  # Required for running as root/in containers
    options.add_argument("--disable-dev-shm-usage")  # Handle limited memory
    options.add_argument("--disable-gpu")  # Required for headless on some systems
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--single-process")  # More stable on limited resource systems

    # Add logging for debugging
    print(f"Chrome version: {os.popen('google-chrome --version').read().strip()}")
    print(f"ChromeDriver version: {os.popen('chromedriver --version').read().strip()}")

    # Let Selenium handle the ChromeDriver
    return webdriver.Chrome(options=options)

def wait_and_remove_overlay(driver):
    """Wait for and remove any overlay that might block interaction"""
    try:
        # Try to accept cookies if the button exists
        accept_button = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
        )
        driver.execute_script("arguments[0].click();", accept_button)
    except:
        # If accept button not found, try to remove overlay directly
        driver.execute_script("""
            var elements = document.getElementsByClassName('onetrust-pc-dark-filter');
            for(var i=0; i<elements.length; i++){
                elements[i].style.display = 'none';
            }
            var banner = document.getElementById('onetrust-banner-sdk');
            if(banner) banner.style.display = 'none';
        """)
    time.sleep(1)

def safe_click(driver, element, element_name=""):
    """Try multiple methods to click an element"""
    print(f"Attempting to click {element_name}...")
    try:
        # Try regular click
        element.click()
        print(f"Regular click successful for {element_name}")
        return True
    except:
        try:
            # Try JavaScript click
            driver.execute_script("arguments[0].click();", element)
            print(f"JavaScript click successful for {element_name}")
            return True
        except:
            try:
                # Try moving to element and clicking
                ActionChains(driver).move_to_element(element).click().perform()
                print(f"ActionChains click successful for {element_name}")
                return True
            except:
                try:
                    # If all else fails, try to remove overlays and click again
                    wait_and_remove_overlay(driver)
                    element.click()
                    print(f"Click after overlay removal successful for {element_name}")
                    return True
                except:
                    print(f"All click attempts failed for {element_name}")
                    return False

def logout(driver):
    """Perform logout operation"""
    print("Starting logout process...")
    try:
        # Click user profile button
        profile_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-analyticsid='heading-panel--user-profile']"))
        )
        if not safe_click(driver, profile_button, "profile button"):
            raise Exception("Failed to click profile button")

        time.sleep(1)  # Wait for dropdown to appear

        # Click logout option
        logout_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-key='logout']"))
        )
        if not safe_click(driver, logout_option, "logout option"):
            raise Exception("Failed to click logout option")

        print("Logout successful!")
        return True
    except Exception as e:
        print(f"Error during logout: {str(e)}")
        return False

def load_accounts(env_file=None):
    """Load account credentials from environment file"""
    # Load specified env file or default to .env
    env_path = env_file or os.getenv("ENV_PATH", ".env")
    print(f"Loading environment from: {env_path}")

    if not os.path.exists(env_path):
        raise ValueError(f"Environment file {env_path} not found")

    # Clear any existing environment variables
    if 'AIVEN_EMAIL' in os.environ:
        del os.environ['AIVEN_EMAIL']
    if 'AIVEN_PASSWORD' in os.environ:
        del os.environ['AIVEN_PASSWORD']

    load_dotenv(dotenv_path=env_path, override=True)

    email = os.getenv('AIVEN_EMAIL')
    password = os.getenv('AIVEN_PASSWORD')

    if not email or not password:
        raise ValueError(f"AIVEN_EMAIL and AIVEN_PASSWORD must be set in {env_path}")

    print(f"Loaded email from {env_path}: {email[:3]}...{email[-8:]}")
    return email, password

def login_to_aiven(driver, email, password):
    """Login to Aiven Console with specific credentials"""
    print(f"Starting login process with email: {email[:3]}...{email[-8:]}")

    try:
        # Navigate to the login page
        print("Navigating to login page...")
        driver.get('https://console.aiven.io/login')
        time.sleep(2)  # Wait for page to fully load

        # Handle any initial overlays
        wait_and_remove_overlay(driver)

        # Wait for and fill email
        print("Waiting for email field...")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.clear()
        email_input.send_keys(email)
        print("Email entered successfully")
        time.sleep(1)

        # Find and click continue button
        print("Looking for continue button...")
        continue_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-analyticsid='login-email--log-in']"))
        )
        if not safe_click(driver, continue_button, "continue button"):
            raise Exception("Failed to click continue button")

        print("Waiting for password field to appear...")
        time.sleep(3)  # Additional wait for page transition

        # Try multiple methods to find and interact with password field
        try:
            # First attempt with explicit wait
            password_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            print("Found password field by name")
        except:
            try:
                # Try finding by XPath
                password_input = driver.find_element(By.XPATH, "//input[@type='password']")
                print("Found password field by type")
            except:
                # Try finding by CSS selector
                password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                print("Found password field by CSS selector")

        # Clear and fill password field
        password_input.clear()
        print("Entering password...")
        password_input.send_keys(password)
        # Try pressing Enter as well
        password_input.send_keys(Keys.RETURN)
        print("Password entered")
        time.sleep(5)  # Wait for login to complete

        return True

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Take screenshot on error
        try:
            driver.save_screenshot(f"error_screenshot_{email[:3]}.png")
            print(f"Error screenshot saved as 'error_screenshot_{email[:3]}.png'")
        except:
            pass
        raise  # Re-raise the exception to be handled by the main function

def main():
    """Main function to handle single account login"""
    parser = argparse.ArgumentParser(description='Aiven Console Login Automation')
    parser.add_argument('--env', type=str, help='Path to environment file (e.g., .env.dev, .env.prod)')
    args = parser.parse_args()

    driver = None
    try:
        # Load the account credentials with specified env file
        email, password = load_accounts(args.env)

        # Initialize driver
        driver = init_driver()

        # Perform login
        print("\nStarting login process...")
        login_to_aiven(driver, email, password)
        print(f"Successfully logged in with account: {email[:3]}...{email[-8:]}")

        # Perform logout
        if not logout(driver):
            raise Exception("Logout failed")

        print("\nLogin and logout complete.")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    finally:
        if driver:
            driver.quit()

    return 0

if __name__ == "__main__":
    exit(main())
