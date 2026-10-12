import requests
import json


def get_data():

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 40.0000,
        "longitude": -74.0000,
        "hourly": ["temperature_2m"],
        "forcast_days": 2,
    }

    response = requests.get(url, params)

    return response.json()


def data_to_file(data):

    with open("test_data.json", "w") as file:

        json.dump(data, file)


def main():
    pass

    data = get_data()

    data_to_file(data)


if __name__ == "__main__":
    main()
