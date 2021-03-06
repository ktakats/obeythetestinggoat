#from django.test import LiveServerTestCase
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, get_user_model
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import os
from datetime import datetime
import sys
import time

DEFAULT_WAIT=5
SCREEN_DUMP_LOCATION=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screendumps')

User=get_user_model()

class FunctionalTest(StaticLiveServerTestCase):
    ###For the staging site
    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url='http://' + arg.split('=')[1]
                cls.against_staging=True
                return
        super(FunctionalTest, cls).setUpClass()
        cls.against_staging=False
        cls.server_url=cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url==cls.live_server_url:
            super(FunctionalTest, cls).tearDownClass()
    #########3

    def setUp(self):
        self.browser=webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
        self.browser.implicitly_wait(DEFAULT_WAIT)

    def tearDown(self):
        if self._test_has_failed():
            if not os.path.exists(SCREEN_DUMP_LOCATION):
                os.makedirs(SCREEN_DUMP_LOCATION)
            for ix, handle in enumerate(self.browser.window_handles):
                self._windowid =ix
                self.browser.switch_to_window(handle)
                self.take_screenshot()
                self.dump_html()
        self.browser.quit()
        super(FunctionalTest, self).tearDown()

    def _test_has_failed(self):

    #    return any(error for (method, error) in self.outcome.errors)
        for method, error in self._resultForDoCleanups.errors:
            if error:
                return True
        for method, failure in self._resultForDoCleanups.failures:
            if failure:
                return True
        return False

    def take_screenshot(self):
        filename=self._get_filename()+'.png'
        print('screenshotting to', filename)
        self.browser.get_screenshot_as_file(filename)

    def dump_html(self):
        filename=self._get_filename()+'.html'
        print('dumping page HTML to', filename)
        with open(filename, 'w') as f:
            f.write(self.browser.page_source)

    def _get_filename(self):
        timestamp=datetime.now().isoformat().replace(':', '.')[:19]
        return '{folder}/{classname}.{method}-window{windowid}-{timestamp}'.format(
            folder=SCREEN_DUMP_LOCATION,
            classname=self.__class__.__name__,
            method=self._testMethodName,
            windowid=self._windowid,
            timestamp=timestamp
        )

    def wait_for(self, function_with_assertion, timeout=DEFAULT_WAIT):
        start_time=time.time()
        while time.time()-start_time<timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        return function_with_assertion()

    def create_pre_authenticated_session(self, email):
        user=User.objects.create(email=email)
        session=SessionStore()
        session[SESSION_KEY]=user.pk
        session[BACKEND_SESSION_KEY]=settings.AUTHENTICATION_BACKENDS[0]
        session.save()
        ## to set a cookie we need to first visit the domain.
        ## 404 pages load the quickest!
        self.browser.get(self.server_url + "/404_no_such_url/")
        self.browser.add_cookie(dict(
            name=settings.SESSION_COOKIE_NAME,
            value=session.session_key,
            path='/',
        ))

    def check_for_row_in_list_table(self, row_text):
        table=self.browser.find_element_by_id('id_list_table')
        rows=table.find_elements_by_tag_name('tr')
        self.assertIn(row_text, [row.text for row in rows])

    def get_item_input_box(self):
        return self.browser.find_element_by_id('id_text')

    def assert_logged_in(self, email):
        self.browser.find_element_by_link_text('Log out')
        navbar=self.browser.find_element_by_css_selector('.navbar')
        self.assertIn(email, navbar.text)

    def assert_logged_out(self, email):
        self.browser.find_element_by_name('email')
        navbar=self.browser.find_element_by_css_selector('.navbar')
        self.assertNotIn(email, navbar.text)
