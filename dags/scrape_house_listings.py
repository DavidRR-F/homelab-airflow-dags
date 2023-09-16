from typing import List, Tuple, Union
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, date
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from plugins.db_models.models import HouseListing, PriceListing, Session
from plugins.firefox_driver.driver import RemoteFirefoxWebDriver
from plugins.firefox_driver.utils.helpers import get_web_elements
from plugins.geolocation.geolocation import get_geolocation
from plugins.utils.helpers import (
    extract_float,
    extract_integer,
    split_address,
)


def extract_house_data(
    marker: WebElement, driver: RemoteFirefoxWebDriver
) -> Tuple[Union[HouseListing, None], Union[PriceListing, None]]:
    try:
        marker.click()
        info: WebElement = get_web_elements(
            driver, By.CLASS_NAME, "top-line-container"
        )[0]
    except Exception as e:
        return None, None
    try:
        specs: List[WebElement] = info.find_elements(
            By.CLASS_NAME, "property-info-container"
        )
        children: List[WebElement] = specs[0].find_elements(By.TAG_NAME, "li")
        city, state, zip_code = split_address(
            info.find_element(By.CLASS_NAME, "property-city-state-zip").text
        )
        address = info.find_element(By.CLASS_NAME, "property-address").text
        if children != []:
            longitude, latitude = get_geolocation(address, city, state, zip_code)
            house = HouseListing(
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

            price = PriceListing(
                address=info.find_element(By.CLASS_NAME, "property-address").text,
                city=city,
                state=state,
                zip=zip_code,
                price=extract_integer(
                    info.find_element(By.CLASS_NAME, "property-price").text
                ),
                date=date.today(),
            )
            return house, price
    except Exception as e:
        return None, None


def insert_data(houses: HouseListing, pricing: PriceListing):
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


def _scraper(url: str):
    houses: list[HouseListing] = []
    pricing: list[PriceListing] = []
    with RemoteFirefoxWebDriver() as driver:
        driver.get(url)
        markers: List[WebElement] = get_web_elements(
            driver, By.CLASS_NAME, "custom-pin-image"
        )
        for marker in markers:
            house, price = extract_house_data(marker, driver)
            if house and price:
                houses.append(house)
                pricing.append(price)
    insert_data(houses, pricing)


with DAG(
    "scrape_house_listings",
    start_date=datetime(2023, 9, 1),
    schedule_interval="@monthly",
    catchup=False,
) as dag:
    base_url = Variable.get("house_listing_url")
    for location in Variable.get("house_listing_locations").split(","):
        for size in Variable.get("house_listing_sizes").split(","):
            county, coords = location.split("?")
            url = f"{base_url}/{county}/{size}/?{coords}"

            scrape_task = PythonOperator(
                task_id=f"scrape_{county}_{size}",
                python_callable=_scraper,
                op_args=[url],
                provide_context=True,
            )

            if prev_task:
                prev_task >> scrape_task

            prev_task = scrape_task
