#from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
import os
from datetime import datetime
import sys

SCREEN_DUMP_LOCATION=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screendumps')

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
        self.browser.implicitly_wait(3)

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
