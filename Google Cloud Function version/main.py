from flask import Request, jsonify
import requests
import pandas as pd
import numpy as np
import geopy.distance
from geopy.geocoders import ArcGIS
import smtplib
from email.mime.text import MIMEText
import urllib.parse

# define variables
gmail_user = "your_email@gmail.com"
gmail_password = "your_password"
reference_address_str = "your_reference_address" # in the format "1 Main St, Nashville, TN"
distance_threshold = 1  # in miles
to_address = "recipient_email@gmail.com"

# url for the active dispatch data
url = "https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Metro_Nashville_Police_Department_Active_Dispatch_Table_view/FeatureServer/0/query"

# define query parameters
query_params = {
    'outFields': '*',
    'where': '1=1',  
    'f': 'geojson' 
}

# geocoding function
def geocode_address(address):
    geolocator = ArcGIS()
    location = geolocator.geocode(address)
    if location:
        return {"latitude": location.latitude, "longitude": location.longitude, "address": location.address}
    else:
        return None

# function to check the distance between two addresses
def check_distance(address1, address2, distance_threshold):
    coords_1 = (address1["latitude"], address1["longitude"])
    coords_2 = (address2["latitude"], address2["longitude"])
    distance = geopy.distance.distance(coords_1, coords_2).miles
    return distance, distance <= distance_threshold

# function to send email using SMTP library
def send_email(subject, message, to_address):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = to_address

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.ehlo()
    server.login(gmail_user, gmail_password)
    server.send_message(msg)
    server.close()
    print(f'Email was sent to {to_address}')

# function to retrieve and process data
def get_data():
    
    response = requests.get(url, params=query_params)
    geojson_content = response.json()

    # convert GeoJSON to dataframe
    features = geojson_content['features']
    data = [feature['properties'] for feature in features]
    df = pd.DataFrame(data)

    # check and replace '/' with '&' for better geocoding accuracy
    df["Location"] = df["Location"].str.replace('/', '&')

    # Old Hickory Blvd runs through different areas so these conditions give better accuracy
    old_hickory = [
        (df["Location"].str.contains("OLD HICKORY BLVD")) & (df["CityName"] == "HERMITAGE"),
        (df["Location"].str.contains("OLD HICKORY BLVD")) & (df["CityName"] == "OLD HICKORY"),
        (df["Location"].str.contains("OLD HICKORY BLVD")) & (df["CityName"] == "BRENTWOOD DAVIDSON COUNTY")
    ]
    areas = [
        df["Location"] + ", Hermitage, TN",
        df["Location"] + ", Old Hickory, TN",
        df["Location"] + ", Brentwood, TN"
    ]
    df["full_address"] = np.select(old_hickory, areas, default=df["Location"] + ", Nashville, TN")

    # geocode reference address
    reference_address = geocode_address(reference_address_str)
    
    # check the distance for each address in the data and send email if within distance threshold
    for index, row in df.iterrows():
        address = geocode_address(row["full_address"])
        if address:
            distance, within_threshold = check_distance(reference_address, address, distance_threshold)
            if within_threshold:
                # convert CallReceivedTime from milliseconds to datetime in Central US Time
                call_received = pd.to_datetime(row["CallReceivedTime"], unit='ms', origin='unix')
                call_received = call_received.tz_localize('UTC').tz_convert('America/Chicago')
                call_received_formatted = call_received.strftime("%m-%d-%Y %I:%M %p")
                rounded_distance = round(distance, 2)
                subject = "Alert: " + row["IncidentTypeName"] + " " + str(rounded_distance) + " mi away"
                message = "Incident Type: " + row["IncidentTypeName"] + "\nCall Received: " + call_received_formatted + "\nCity: " + row["CityName"]
            
                # get the full address from ArcGIS geocoding result
                full_address = address["address"]
            
                # add full address to the email message
                message += f"\nFull Address: {full_address}"
            
                # check if '&' exists in the address
                if '&' in row["Location"]:
                    # Format coordinates 
                    latitude = address["latitude"]
                    longitude = address["longitude"]
                    coordinates = f"{latitude},{longitude}"
                    
                    # create Google Maps link with coordinates for cross streets
                    street_view = f"http://maps.google.com/maps?q=&layer=c&cbll={coordinates}"
                else:
                    # encode spaces in the full address
                    encoded_full_address = urllib.parse.quote(full_address)

                    # create Google Maps link with the encoded full address
                    street_view = f"http://maps.google.com/maps?q={encoded_full_address}"

                # add Google Maps link to the email message
                message += f"\nStreet View: {street_view}"
        
                send_email(subject, message, to_address)
    
    # return a JSON response
    response_data = {"message": "Data retrieved and processed successfully"}
    return jsonify(response_data)
