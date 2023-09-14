from typing import List, Tuple
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import TaskInstance, Variable
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, date

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

from plugins.db_models.models import HouseListing, PriceListing, Session
from plugins.geolocation.geolocation import get_geolocation
from plugins.utils.helpers import (
    extract_float,
    extract_integer,
    split_address,
)


def _scrape_urls():
    remote_webdriver = "http://remote_driver:4444"
    options = Options()
    # options.add_experimental_option("detach", True)
    options.add_argument("--headless")
    # options.add_argument("--incognito")
    options.set_preference("browser.link.open_newwindow.restriction", 0)
    # options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920x1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    with webdriver.Remote(
        command_executor=f"{remote_webdriver}", options=options
    ) as driver:
        houses: list[HouseListing] = []
        pricing: list[PriceListing] = []
        base_url: str = Variable.get("house_listing_url")
        locations: str = Variable.get("house_listing_locations")
        sizes: str = Variable.get("house_listing_sizes")
        for location in locations.split(","):
            for size in sizes.split(","):
                county, coords = location.split("?")
                url = f"{base_url}/{county}/{size}/?{coords}"
                print(url)
                driver.get(url)
                wait = WebDriverWait(driver, 10)
                markers: List[WebElement] = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "custom-pin-image")
                    )
                )
                for marker in markers:
                    try:
                        marker.click()
                        wait = WebDriverWait(driver, 10)
                        info = wait.until(
                            EC.presence_of_all_elements_located(
                                (By.CLASS_NAME, "top-line-container")
                            )
                        )
                        info: WebElement = info[0]
                        try:
                            specs: List[WebElement] = info.find_elements(
                                By.CLASS_NAME, "property-info-container"
                            )
                            children: List[WebElement] = specs[0].find_elements(
                                By.TAG_NAME, "li"
                            )
                            city, state, zip_code = split_address(
                                info.find_element(
                                    By.CLASS_NAME, "property-city-state-zip"
                                ).text
                            )
                            address = info.find_element(
                                By.CLASS_NAME, "property-address"
                            ).text
                            if children != []:
                                longitude, latitude = get_geolocation(
                                    address, city, state, zip_code
                                )
                                houses.append(
                                    HouseListing(
                                        address=address,
                                        city=city,
                                        state=state,
                                        zip=zip_code,
                                        beds=extract_integer(children[0].text),
                                        baths=extract_float(children[1].text),
                                        sqft=extract_integer(children[2].text),
                                        longitude=longitude,
                                        latitude=latitude,
                                    )
                                )
                                pricing.append(
                                    PriceListing(
                                        address=info.find_element(
                                            By.CLASS_NAME, "property-address"
                                        ).text,
                                        city=city,
                                        state=state,
                                        zip=zip_code,
                                        price=extract_integer(
                                            info.find_element(
                                                By.CLASS_NAME, "property-price"
                                            ).text
                                        ),
                                        date=date.today(),
                                    )
                                )
                        except Exception as e:
                            continue
                    except Exception as e:
                        continue
        print(len(houses))
        session = Session()
        house_dicts = [
            {
                key: value
                for key, value in house.__dict__.items()
                if not key.startswith("_sa_")
            }
            for house in houses
        ]
        stmt_house = (
            insert(HouseListing)
            .values(house_dicts)
            .on_conflict_do_nothing(index_elements=["address", "city", "state", "zip"])
        )
        price_dicts = [
            {
                key: value
                for key, value in price.__dict__.items()
                if not key.startswith("_sa_")
            }
            for price in pricing
        ]
        stmt_pricing = (
            insert(PriceListing)
            .values(price_dicts)
            .on_conflict_do_nothing(
                index_elements=["address", "city", "state", "zip", "date"]
            )
        )

        try:
            session.execute(stmt_house)
            session.execute(stmt_pricing)
            session.commit()
        except Exception as e:
            print(e)
        finally:
            session.close()


with DAG(
    "house_listing",
    start_date=datetime(2021, 1, 1),
    schedule_interval="@monthly",
    catchup=False,
) as dag:
    scrape_urls = PythonOperator(
        task_id="scrape_urls",
        python_callable=_scrape_urls,
    )

    scrape_urls
