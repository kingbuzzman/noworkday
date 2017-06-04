import os
import keyring
import getpass
import random
import time
import logging

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
    Generates 3 time slots based on the amount of hours
    """
    log.info('Generating {} hours worth of data'.format(hours))
    percents = {
        'guide': 0,
        'navigate': 0,
        # set a base for the inputs
        'admin': quarter_round(random.triangular(6, 20, 6))
    }

    # Randomly loop over the remaining 2 slots and fill them out
    for key in sorted(['guide', 'navigate'], key=lambda x: random.random()):
        high = float(str((100 - (sum(percents.values())))))
        percents[key] = quarter_round(random.triangular(0, high, high))

    log.debug('First iteration {} having a total of {} percents'.format(percents, sum(percents.values())))

    total_sum = sum(percents.values())
    while total_sum != 100:
        high = (100 - total_sum)
        percents[random.sample(percents.keys(), 1)[0]] += quarter_round(float(random.randrange(0, high * 100)) / 100)
        total_sum = sum(percents.values())

        log.debug('Iteration yielded {} with a sum of {}'.format(percents, sum(percents.values())))

    distribution = {}
    minutes = float(hours) * 60
    for key, percent in percents.iteritems():
        distribution[key] = quarter_round(minutes * (float(percent) / 100) / 60)

    log.debug('Created {} with a total hour count of {}'.format(distribution, sum(distribution.values())))

    return distribution


def week_distribution(min_daily_hours=8, max_daily_hours=13, days_in_week=5):
    """
    Generate a list of hours worked for an entire week
    """
    log.info('Generating {} day(s) worth of timesheets with a minimum of {} hours and a maximum of {} hours'.format(
        days_in_week, min_daily_hours, max_daily_hours))

    for _ in xrange(days_in_week):
        daily_hours = quarter_round(random.uniform(min_daily_hours, max_daily_hours))
        yield time_distribution(daily_hours)


def get_password(user):
    """
    Will use the OSX KeyChain to get and store your password
    """
    def ask_password():
        print('Please enter your Advisory Board SSO password.')
        return getpass.getpass('Password:')

    try:
        password = keyring.get_password('workday', user)

        if password is None:
            password = ask_password()
            try:
                keyring.set_password('workday', user, password)
            except keyring.errors.PasswordSetError:
                log.warn('Could not save password in KeyChain')
    except keyring.backends._OS_X_API.Error:
        print('You should really consider saying "Allow" or "Always Allow" and not being scur\'d all the time')
        print('The password will NOT be saved.')
        password = ask_password()

    return password


def open_submenu(driver, time_type):
    """
    Open the dialog's drop down menu
    """
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

    canary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--incognito')

    # support for headless chrome
    if os.path.isfile(canary_location):
        chrome_options.binary_location = canary_location
        chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(chrome_options=chrome_options)
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
    # this_week_button = "((//span[contains(text(), 'Last Week (')])/..)[last()]"
    get_element(driver, this_week_button).click()

    log.info('Clicking on "Enter Time"')
    enter_time = "(//span[contains(text(), 'Enter Time')])[last()]"
    get_element(driver, enter_time).click()

    enter_time2 = "(//div[contains(text(), 'Enter Time')])[last()]"
    get_element(driver, enter_time2).click()

    days_in_week = '//*[@id="wd-TimeEntry-NO_METADATA_ID"]/div/div[1]/ul/li[{}]'
    days_in_week_content = '//*[contains(@id, "tabPanel_")]/div[{}]//label[contains(text(), "Time Type")]/../../../../../../../../div[{}]'
    for counter, distributions in enumerate(week_distribution()):
        # Click on the page to open the time dialog
        log.info('Selecting the date')
        element = get_element(driver, days_in_week.format(counter + 1))
        element.click()

        for distribution_counter, _ in enumerate(distributions.iteritems()):
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
            element.send_keys(Keys.BACKSPACE*10)
            element.send_keys(str(hours))

    log.info('Saving all the data')
    get_element(driver, "(//button/span[text() = 'OK'])/..").click()
    time.sleep(5)

    driver.close()


def get_element(driver, xpath):
    """
    A total hack, the way that workday handles its UI is monstrous, and it will override the same element a couple of
    times a second, thus this hack was created.

    TODO: Fix this
    """
    log.debug('Selecting: {}'.format(xpath))
    try:
        element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    except:
        try:
            element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except:
            element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
    time.sleep(0.2)  # TODO: find a better solution
    return element


if __name__ == '__main__':
    main()
