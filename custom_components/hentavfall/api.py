import asyncio
import logging
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

from .const import BASE_URL, WASTE_TYPES

_LOGGER = logging.getLogger(__name__)

class HentavfallApi:
    """Class to fetch and parse waste collection data."""

    def __init__(self, guid, session: aiohttp.ClientSession):
        self.guid = guid
        self.url = BASE_URL.format(guid)
        self.session = session

    async def fetch_data(self):
        """Fetch and parse waste collection schedule."""
        try:
            async with self.session.get(self.url) as response:
                response.raise_for_status()
                html = await response.text()
                return self._parse_html(html)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching data from %s: %s", self.url, err)
            return None
        except Exception as err:
            _LOGGER.error("An unexpected error occurred: %s", err)
            return None

    def _parse_html(self, html):
        """Parse the HTML and extract waste collection dates."""
        soup = BeautifulSoup(html, 'html.parser')
        calendar_table = soup.find("table", class_="js-waste-calendar")
        
        if not calendar_table:
            _LOGGER.warning("Could not find waste calendar table in HTML.")
            return {}

        schedule = {}
        monthly_sections = calendar_table.find_all("tbody")

        for section in monthly_sections:
            month_year_str = section.get('data-month')
            if not month_year_str:
                continue
            
            try:
                _, year = month_year_str.split('-')
            except ValueError:
                _LOGGER.warning("Could not parse year from data-month: %s", month_year_str)
                continue

            rows = section.find_all("tr", class_="waste-calendar__item")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) != 2:
                    continue

                # Date parsing
                date_str = cells[0].text.strip().split(' - ')[0]
                full_date_str = f"{date_str}.{year}"
                
                try:
                    pickup_date = datetime.strptime(full_date_str, '%d.%m.%Y').date()
                except ValueError:
                    _LOGGER.warning("Could not parse date: %s", full_date_str)
                    continue

                # Waste type parsing
                images = cells[1].find_all("img")
                for img in images:
                    src = img.get('src', '')
                    for key, name in WASTE_TYPES.items():
                        if f"/{key}.svg" in src:
                            if name not in schedule:
                                schedule[name] = []
                            if pickup_date not in schedule[name]:
                                schedule[name].append(pickup_date)
        
        # Sort dates for each waste type
        for waste_type in schedule:
            schedule[waste_type].sort()
            
        return schedule