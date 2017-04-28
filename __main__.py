import os
import keyring
import getpass
# import contextlib
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of


def get_password(user):
    """
    Will use the OSX KeyChain to get and store your password
    """
    password = keyring.get_password('workday', user)

    if password is None:
        password = getpass.getpass('Password:')
        keyring.set_password('workday', user, password)

    return password


# # @contextlib.contextmanager
# def wait_for_page_load(timeout=20):
#     print("Waiting for page to load at {}.".format(driver.current_url))
#     old_page = driver.find_element_by_tag_name('html')
#     # yield
#     WebDriverWait(driver, timeout).until(staleness_of(old_page))


user = os.getenv('USER')
password = get_password(user)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")

driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get("https://{}:{}@sso.advisory.com/workday/login".format(user, password))

time_icon = "//span[text() = 'Time']"
element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, time_icon)))
element.click()

this_week_button = "(//span[contains(text(), 'This Week')])[2]/.."
element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, this_week_button)))
element.click()

# import ipdb; ipdb.set_trace()
time.sleep(5)
# # wait_for_page_load()
#
# import ipdb; ipdb.set_trace()
# # Find and click on the "Time" span
# driver.find_elements_by_xpath("//span[text() = 'Time']")[0].click()


# wait_for_page_load()





# assert "Python" in driver.title
# elem = driver.find_element_by_name("q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
driver.close()
