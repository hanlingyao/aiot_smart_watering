import json

from .irrigation_plan import irrigation_plan
from .plant_recognition_module import identify_plant_plantnet, extract_scientific_name


PLANTNET_API_KEY = ""

def check_plant_name():
    try:
        with open("sci_name.txt", "r") as f:
            plant_name = f.read()
            if plant_name == "":
                with open("sci_name.txt", "w") as f:
                    image_path = "image.jpg"
                    plantnet_result = identify_plant_plantnet(image_path, PLANTNET_API_KEY)
                    plant_name = extract_scientific_name(plantnet_result)
                    f.write(plant_name)
    except FileNotFoundError:
        with open("sci_name.txt", "w") as f:
            image_path = "image.jpg"
            plantnet_result = identify_plant_plantnet(image_path, PLANTNET_API_KEY)
            plant_name = extract_scientific_name(plantnet_result)
            f.write(plant_name)
    return plant_name

def get_pot_info():
    with open("pot_info.json","r") as f:
        pot_info = json.load(f)
    pot_diameter, pot_height = pot_info["pot_diameter"], pot_info["pot_height"]
    return pot_diameter, pot_height

def main():

    # Check if the plant is identified    
    plant_name = check_plant_name()
    print("✅ Plant Name:", plant_name)

    # Get Pot Info
    pot_diameter, pot_height = get_pot_info()

    return irrigation_plan(plant_name=plant_name,
                           image_path="image.jpg",
                    pot_diameter=pot_diameter,
                    pot_height=pot_height,
                    )



if __name__ == "__main__":
    main()
