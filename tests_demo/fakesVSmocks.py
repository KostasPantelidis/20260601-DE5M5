# Fakes: When we can build a simple in-memory replacement
# Mocks: When we just want to verify that the call happens


# MOCKING

import requests
from unittest.mock import patch


def get_weather(city):
    result = requests.get(
        f"URL/weather/{city}"
    )
    return result.json()


@patch("requests.get")
def test_weather(mock_get):
    mock_get.return_value.json.return_value = {
        "temp":20
    }

    result = get_weather("London")

    assert result["temp"] == 20

test_weather()

print("Tests Run")