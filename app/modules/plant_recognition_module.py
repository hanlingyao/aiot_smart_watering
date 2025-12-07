# identify_plant.py
import requests

def identify_plant_plantnet(image_path: str, api_key: str) -> dict:
    base_url = "https://my-api.plantnet.org/v2/identify/all"

    params = {
        "api-key": api_key,
        "include-related-images": "false",
        "no-reject": "false",
        "nb-results": 1,
        "detailed": "false",
        "lang": "en",
    }

    data = {
        "organs": "auto"   #"flower" / "fruit" / "bark" / "auto"
    }

    with open(image_path, "rb") as f:
        files = [
            ("images", (image_path, f, "image/jpeg"))
        ]

        resp = requests.post(
            base_url,
            params=params,
            data=data,
            files=files
        )

    resp.raise_for_status()
    return resp.json()


def extract_scientific_name(plantnet_result: dict) -> str | None:
    try:
        first_result = plantnet_result["results"][0]
        sci_name = first_result["species"]["scientificName"]
        return sci_name
    except (KeyError, IndexError, TypeError):
        return None


if __name__ == "__main__":
    api_key = "2b102oHW1S6c8yhVFhh7fJofzO"
    image_path = "test_plant.jpg"

    result = identify_plant_plantnet(image_path, api_key)
    sci_name = extract_scientific_name(result)
    print("Plant Name", sci_name)
