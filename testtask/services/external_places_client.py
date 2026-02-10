import requests


EXTERNAL_API_BASE_URL = "https://api.artic.edu/api/v1"


class ExternalPlaceNotFound(Exception):
    pass


class ExternalAPIError(Exception):
    pass


def assert_place_exists(external_id: int, timeout_s: float = 5.0) -> None:
    """
    Validates existence of an external place using the configured provider.
    Currently backed by Art Institute of Chicago API.
    """
    url = f"{EXTERNAL_API_BASE_URL}/artworks/{external_id}"

    try:
        response = requests.get(url, timeout=timeout_s)
    except requests.RequestException as e:
        raise ExternalAPIError(f"External API request failed: {e}") from e

    if response.status_code == 404:
        raise ExternalPlaceNotFound(f"External place {external_id} not found")

    if response.status_code >= 400:
        raise ExternalAPIError(
            f"External API returned status {response.status_code}"
        )