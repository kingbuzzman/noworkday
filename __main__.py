import os
import keyring
import getpass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def get_password(user):
    """
    Will use the OSX KeyChain to get and store your password
    """
    password = keyring.get_password('workday', user)

    if password is None:
        password = getpass.getpass('Password:')
        keyring.set_password('workday', user, password)

    return password



user = os.getenv('USER')
password = get_password(user)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")

driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get("https://{}:{}@sso.advisory.com/workday/login".format(user, password))

# assert "Python" in driver.title
# elem = driver.find_element_by_name("q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
driver.close()
