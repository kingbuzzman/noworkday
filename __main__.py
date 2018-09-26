import os
import getpass
import random
import time
import logging
import subprocess

from decimal import Decimal

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(console)


def quarter_round(num):
    """
    Takes in a float and rounds it to the nearest 1/4
    """
    return Decimal(round(num * 4) / 4)


def time_distribution(hours):
    """
    Generates 2 time slots based on the amount of hours
    """
    log.info('Generating {} hours worth of data'.format(hours))
    CAP_PERCENT = random.triangular(45, 70, 60)
    percents = {
        'student': CAP_PERCENT,
        'admin': 100 - CAP_PERCENT
    }

    distribution = {}
    minutes = float(hours) * 60
    for key, percent in percents.items():
        distribution[key] = quarter_round(minutes * (float(percent) / 100) / 60)

    log.debug('Created {} with a total hour count of {}'.format(distribution, sum(distribution.values())))

    return distribution


def week_distribution(min_daily_hours=8, max_daily_hours=13, days_in_week=5):
    """
    Generate a list of hours worked for an entire week
    """
    log.info('Generating {} day(s) worth of timesheets with a minimum of {} hours and a maximum of {} hours'.format(
        days_in_week, min_daily_hours, max_daily_hours))

    for _ in range(days_in_week):
        daily_hours = quarter_round(random.uniform(min_daily_hours, max_daily_hours))
        yield time_distribution(daily_hours)


def get_password(user):
    """
    Will use the OSX KeyChain to get your password
    """
    def ask_password():
        print('Please enter your Advisory Board SSO password.')
        return getpass.getpass('Password:')

    command = '/usr/bin/security find-generic-password -wl abcemployees'.split(' ')
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    password = process.stdout.read().strip().decode()
    if password is None:
        password = ask_password()

    return password


def open_submenu(driver, time_type):
    """
    Open the dialog's drop down menu
    """
    # Make selection
    if time_type == 'admin':
        submenu_dropdown(driver, "(//div[text() = '{}'])[last()]", 'Project Plan Tasks',
                         'Education Advisory Board', 'All', 'Education Advisory Board > All > Admin/Other')
    elif time_type == 'student':
        submenu_dropdown(driver, "(//div[contains(text(), '{}')])[last()]", 'Project Plan Tasks',
                         'Education Advisory Board', 'EAB',
                         'Education Advisory Board > EAB > Student Platform')


def submenu_dropdown(driver, xpath_format, *menus):
    """
    Traverse the dropdown menus
    """
    for menu in menus:
        log.debug('Seleting submenu item: {}'.format(menu))
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
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://{}:{}@sso.advisory.com/workday/login'.format(user, password))

    try:
        # SSO added an in between page that sometimes shows up and prompts the user to click Login
        get_element(driver, "//input[@id = 'Login']").click()
    except:
        pass

    log.info('Clicking on the "Time" section/icon')
    time_icon = "//span[text() = 'Time']"
    get_element(driver, time_icon).click()

    log.info('Clicking on the "This Week"')
    this_week_button = "((//span[contains(text(), 'This Week (')])/..)[last()]"
    get_element(driver, this_week_button).click()

    # # Two weeks ago
    # get_element(driver, "((//span[contains(text(), 'Last Week (')])/..)[last()]").click()
    # time.sleep(2)

    log.info('Clicking on "Enter Time"')
    get_element(driver, "(//span[contains(text(), 'Enter Time')])[last()]/..", wait_time=30).click()
    # # Sometimes you need this one
    # get_element(driver, "//span[contains(text(), 'Enter Time')]").click()
    get_element(driver, "(//div[contains(text(), 'Enter Time')])[last()]").click()

    days_in_week = '//*[contains(@id, "wd-TimeEntry-NO_METADATA_ID")]/div/div[1]/ul/li[{}]'
    days_in_week_content = '//*[contains(@id, "tabPanel_")]/div[{}]//label[contains(text(), "Time Type")]/../../../../../../../../div[{}]'
    for counter, distributions in enumerate(week_distribution()):
        # Click on the page to open the time dialog
        log.info('Selecting the date')
        element = get_element(driver, days_in_week.format(counter + 1))
        element.click()

        for distribution_counter, _ in enumerate(distributions.items()):
            time_type, hours = _
            log.debug('Opening the menu for Time Type: {}'.format(time_type))

            dropdown = '{}//label[contains(text(), "Time Type")]/../../div[2]'.format(
                days_in_week_content.format(counter + 1, distribution_counter + 1),
                distribution_counter + 1
            )
            element = get_element(driver, dropdown)
            driver.execute_script("return arguments[0].scrollIntoView(true);", element)
            element.click()

            open_submenu(driver, time_type)

            log.debug('Adding hours')
            input_hours = '{}//label[contains(text(), "Quantity")]/../../div[2]//input'.format(
                days_in_week_content.format(counter + 1, distribution_counter + 1),
                distribution_counter + 1
            )
            element = get_element(driver, input_hours)
            element.send_keys(Keys.BACKSPACE * 10)
            element.send_keys(str(hours))

    log.info('Saving all the data')
    get_element(driver, "(//button/span[text() = 'OK'])/..").click()
    time.sleep(5)

    driver.close()


def get_element(driver, xpath, wait_time=5):
    """
    A total hack, the way that workday handles its UI is monstrous, and it will override the same element a couple of
    times a second, thus this hack was created.

    TODO: Fix this
    """
    log.debug('Selecting: {}'.format(xpath))
    try:
        element = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except:
        try:
            element = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except:
            element = WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    time.sleep(0.2)  # TODO: find a better solution
    return element


if __name__ == '__main__':
    main()
