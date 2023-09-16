from selenium.webdriver import Remote
from selenium.webdriver.firefox.options import Options


class RemoteFirefoxWebDriver:
    def __init__(self, remote_url="http://remote_driver:4444"):
        self.remote_url = remote_url
        self.options = self._setup_options()

    def _setup_options(self):
        options = Options()
        options.add_argument("--headless")
        options.set_preference("browser.link.open_newwindow.restriction", 0)
        options.add_argument("--window-size=1920x1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        return options

    def __enter__(self):
        self.driver = Remote(command_executor=self.remote_url, options=self.options)
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()
