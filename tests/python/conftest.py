import pytest
import requests
from os import environ
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

import urllib3
urllib3.disable_warnings()


def edge_options(platform_name):
    options = webdriver.EdgeOptions()
    options.set_capability('platformName', platform_name)
    return options


def firefox_options(platform_name):
    options = webdriver.FirefoxOptions()
    options.set_capability('platformName', platform_name)
    return options


def chrome_options(platform_name):
    options = webdriver.ChromeOptions()
    options.set_capability('platformName', platform_name)
    return options


desktop_browsers = [
    edge_options('Windows 10'),
    edge_options('macOS 11.00'),
    chrome_options('Windows 10'),
    chrome_options('macOS 11.00'),
    firefox_options('Windows 10'),
    firefox_options('macOS 11.00')]

build_tag = f'run_your_tests_anywhere_{datetime.now().strftime("%d.%m.%Y-%H:%M")}'
tunnel_name = environ.get('SAUCE_TUNNEL_NAME', 'python-tests')


@pytest.fixture(params=desktop_browsers)
def desktop_web_driver(request):
    test_name = request.node.name
    username = environ.get('SAUCE_USERNAME', None)
    access_key = environ.get('SAUCE_ACCESS_KEY', None)

    selenium_endpoint = "https://{}:{}@ondemand.us-west-1.saucelabs.com/wd/hub".format(username, access_key)

    options = request.param
    options.set_capability('sauce:build', build_tag)
    options.set_capability('sauce:name', test_name)
    options.set_capability('sauce:tunnelIdentifier', tunnel_name)

    browser = webdriver.Remote(
        command_executor=selenium_endpoint,
        options=options,
        keep_alive=True
    )

    if browser is None:
        raise WebDriverException("Never created!")

    yield browser

    # Teardown starts here
    # report results
    # use the test result to send the pass/fail status to Sauce Labs
    sauce_result = "failed" if request.node.rep_call.failed else "passed"
    browser.execute_script("sauce:job-result={}".format(sauce_result))
    browser.quit()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # this sets the result as a test attribute for Sauce Labs reporting.
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set an report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    print("Cleaning database...")
    sut_host = environ.get('SUT_HOST', 'localhost')
    response = requests.delete(f'http://{sut_host}:3000/items')
    assert response.status_code == 200
