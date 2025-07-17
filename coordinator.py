import random
import httpx
import logging
import json
from datetime import datetime, date, timedelta
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, CONF_HOST, CONF_PORT

_LOGGER = logging.getLogger(__name__)

def _get_easter_date(year: int) -> date:
    """Calculates the date of Easter Sunday for a given year."""
    # Meeus/Jones/Butcher algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def _get_thanksgiving_date(year: int) -> date:
    """Calculates the date of US Thanksgiving (4th Thursday in November)."""
    nov1 = date(year, 11, 1)
    day_of_week = nov1.weekday()
    days_to_thursday = (3 - day_of_week + 7) % 7
    first_thursday = nov1 + timedelta(days=days_to_thursday)
    # Thanksgiving is 3 weeks after the first Thursday
    return first_thursday + timedelta(weeks=3)


def get_active_playlist(hass: HomeAssistant) -> str | None:
    """Determine the active playlist based on the current date and schedule."""
    schedule_path = hass.config.path("custom_components", DOMAIN, "playlist_schedule.json")
    try:
        with open(schedule_path, 'r') as f:
            schedule = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        _LOGGER.error(f"Could not load or parse playlist_schedule.json: {e}")
        return None

    today = datetime.now().date()
    today_str = today.strftime("%d.%m")
    year = today.year

    # Map of dynamic holiday names to their calculation functions
    dynamic_holiday_calculators = {
        "easter": _get_easter_date,
        "thanksgiving_us": _get_thanksgiving_date,
    }

    for playlist, config in schedule.items():
        playlist_type = config.get("type")

        if playlist_type == "range":
            try:
                start = datetime.strptime(config["start"], "%d.%m").date().replace(year=year)
                end = datetime.strptime(config["end"], "%d.%m").date().replace(year=year)
                if start > end:  # Handles year-crossing ranges
                    if today >= start or today <= end:
                        _LOGGER.debug(f"Date {today_str} is in year-crossing range for '{playlist}'")
                        return playlist
                elif start <= today <= end:
                    _LOGGER.debug(f"Date {today_str} is in range for '{playlist}'")
                    return playlist
            except (ValueError, KeyError) as e:
                _LOGGER.warning(f"Invalid range config for playlist '{playlist}': {e}")
                continue
        
        elif playlist_type == "dates":
            if today_str in config.get("dates", []):
                _LOGGER.debug(f"Date {today_str} matches a date for '{playlist}'")
                return playlist

        elif playlist_type == "dynamic":
            holiday_name = config.get("holiday")
            if holiday_name in dynamic_holiday_calculators:
                calculated_date = dynamic_holiday_calculators[holiday_name](year)
                if today == calculated_date:
                    _LOGGER.debug(f"Today is {holiday_name} ({calculated_date.strftime('%d.%m')}), activating playlist '{playlist}'")
                    return playlist
            else:
                _LOGGER.warning(f"Unknown dynamic holiday specified: '{holiday_name}'")


    return None

async def setup_table_service(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    base_url = f"http://{host}:{port}"

    async def run_pattern(file_name: str):
        """Helper to run a specific pattern."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {"file_name": file_name, "pre_execution": "adaptive"}
                run_resp = await client.post(f"{base_url}/run_theta_rho", json=payload)
                run_resp.raise_for_status()
                _LOGGER.info(f"Started pattern {file_name} on {host}:{port}")
        except httpx.RequestError as e:
            _LOGGER.error(f"Error communicating with DuneWeaver at {base_url}: {e}")
            raise HomeAssistantError(f"Error running pattern on {host}:{port}: {e}") from e

    async def get_random_pattern_from_playlist(playlist_name: str) -> str | None:
        """Get a random pattern file name from a given playlist."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base_url}/get_playlist?name={playlist_name}")
                if resp.status_code == 404 or resp.json() is None:
                    _LOGGER.info(f"Playlist '{playlist_name}' not found on {host}:{port}.")
                    return None
                resp.raise_for_status()
                playlist_data = resp.json()
                files = playlist_data.get("files")
                if files:
                    return random.choice(files)
                _LOGGER.warning(f"Playlist '{playlist_name}' on {host}:{port} is empty.")
                return None
        except (httpx.RequestError, json.JSONDecodeError) as e:
            _LOGGER.error(f"Error getting playlist '{playlist_name}' from {host}:{port}: {e}")
        return None

    async def get_random_pattern_from_all() -> str | None:
        """Get a random pattern from all available patterns."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base_url}/list_theta_rho_files")
                resp.raise_for_status()
                files = resp.json()
                if files:
                    return random.choice(files)
                _LOGGER.warning(f"No theta-rho files found on {host}:{port}")
                return None
        except (httpx.RequestError, json.JSONDecodeError) as e:
            _LOGGER.error(f"Error getting all patterns from {host}:{port}: {e}")
        return None

    async def handle_run_random(call: ServiceCall):
        """Handle the run_random_pattern service call."""
        file_name = await get_random_pattern_from_all()
        if file_name:
            await run_pattern(file_name)
        else:
            _LOGGER.error(f"Could not find any pattern to run on {host}:{port}")

    async def handle_run_fitting(call: ServiceCall):
        """Handle the run_fitting_pattern service call."""
        _LOGGER.info("Determining fitting pattern to run...")
        active_playlist = get_active_playlist(hass)
        pattern_to_run = None

        if active_playlist:
            _LOGGER.info(f"Active special playlist found: '{active_playlist}'")
            pattern_to_run = await get_random_pattern_from_playlist(active_playlist)

        if not pattern_to_run:
            _LOGGER.info("No special playlist active or pattern found, trying 'Neutral' playlist.")
            pattern_to_run = await get_random_pattern_from_playlist("Neutral")

        if not pattern_to_run:
            _LOGGER.info("No 'Neutral' playlist or pattern found, falling back to random from all.")
            pattern_to_run = await get_random_pattern_from_all()

        if pattern_to_run:
            await run_pattern(pattern_to_run)
        else:
            _LOGGER.error(f"Could not find any pattern to run on {host}:{port}")

    hass.services.async_register(DOMAIN, f"run_random_pattern_{entry.entry_id}", handle_run_random)
    hass.services.async_register(DOMAIN, f"run_fitting_pattern_{entry.entry_id}", handle_run_fitting)
