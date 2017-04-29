import os
import keyring
import getpass
import random
import time

from decimal import Decimal

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def quarter_round(num):
    """
    Takes in a float and rounds it to the nearest 1/4
    """
    return Decimal(round(num * 4) / 4)


def time_distribution(hours):
    """
    Generates 3 time slots based on the amount of hours
    """
    percents = {
        'guide': 0,
        'navigate': 0,
        # set a base for the inputs
        'admin': quarter_round(float(random.randrange(200, 4000)) / 100)
    }

    # Randomly loop over the remaining 2 slots and fill them out
    for key in sorted(['guide', 'navigate'], key=lambda x: random.random()):
        high = (10000 - (sum(percents.values()) * 100))
        percents[key] = quarter_round(random.randrange(0, high) / 100)

    total_sum = sum(percents.values())
    while total_sum != 100:
        high = (100 - total_sum)
        percents[random.sample(percents.keys(), 1)[0]] += quarter_round(float(random.randrange(0, high * 100)) / 100)
        total_sum = sum(percents.values())

    distribution = {}
    minutes = float(hours) * 60
    for key, percent in percents.iteritems():
        distribution[key] = quarter_round(minutes * (float(percent) / 100) / 60)

    return distribution


def week_distribution(min_daily_hours=8, max_daily_hours=13, days_in_week=5):
    """
    Generate a list of hours worked for an entire week
    """
    for _ in xrange(days_in_week):
        daily_hours = quarter_round(random.uniform(min_daily_hours, max_daily_hours))
        yield time_distribution(daily_hours)


def get_password(user):
    """
    Will use the OSX KeyChain to get and store your password
    """
    password = keyring.get_password('workday', user)

    if password is None:
        password = getpass.getpass('Password:')
        keyring.set_password('workday', user, password)

    return password


def open_submenu(driver, time_type):
    """
    Open the dialog's drop down menu
    """
    time_type_label = "(//label[contains(text(), 'Time Type')]/../../div)[2]/div/span/div"
    get_element(driver, time_type_label).click()

    # try:
    if True:
        # Make selection
        if time_type == 'admin':
            submenu_dropdown(driver, "(//div[text() = '{}'])[last()]", 'Project Plan Tasks',
                            'Education Advisory Board', 'All', 'Education Advisory Board > All - Admin/Other')
        elif time_type == 'guide':
            submenu_dropdown(driver, "(//div[text() = '{}'])[last()]", 'Project Plan Tasks',
                             'Education Advisory Board', 'EAB',
                             'Education Advisory Board > EAB - Guide  (01/01/2017 - 12/31/2017)')
        elif time_type == 'navigate':
            submenu_dropdown(driver, "(//div[text() = '{}'])[last()]", 'Project Plan Tasks',
                             'Education Advisory Board', 'EAB',
                             'Education Advisory Board > EAB - Navigate  (01/01/2017 - 12/31/2017)')
    # except:
    #     open_submenu(driver, time_type)


def submenu_dropdown(driver, xpath_format, *menus):
    """
    Traverse the dropdown menus
    """
    for menu in menus:
        xpath = xpath_format.format(menu)
        element = get_element(driver, xpath)

        action = webdriver.common.action_chains.ActionChains(driver)
        action.move_to_element(element)
        action.click()
        action.perform()

        time.sleep(.8)


def main():
    user = os.getenv('USER')
    password = get_password(user)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("https://{}:{}@sso.advisory.com/workday/login".format(user, password))

    # get_element(driver, "(//div[@role = 'alertdialog']/descendant::button)[1]").click()

    time_icon = "//span[text() = 'Time']"
    get_element(driver, time_icon).click()

    this_week_button = "((//span[contains(text(), 'This Week (')])/..)[last()]"
    get_element(driver, this_week_button).click()

    days_in_week = "(//div[contains(@class, 'day-separator')])[{}]"
    for counter, distributions in enumerate(week_distribution()):
        for time_type, hours in distributions.iteritems():
            element = get_element(driver, days_in_week.format(counter + 1))

            # Click on the page to open the time dialog
            action = webdriver.common.action_chains.ActionChains(driver)
            action.move_to_element_with_offset(element, 5, element.size['height'] - 70)
            action.click()
            action.perform()

            ok_button = "(//button/span[text() = 'OK'])/.."
            ok_button_element = get_element(driver, ok_button)

            open_submenu(driver, time_type)

            time.sleep(1.5)  # TODO: find a better solution

            hours_input = "(//label[contains(text(), 'Hour')]/../../div)[2]/*/input"
            hours_input_element = get_element(driver, hours_input)
            hours_input_element.send_keys(Keys.BACKSPACE*10)
            hours_input_element.send_keys(str(hours))

            ok_button_element.click()

            time.sleep(5)  # TODO: find a better solution

    driver.close()


def get_element(driver, xpath):
    try:
        return WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except:
        return WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))


if __name__ == '__main__':
    main()
