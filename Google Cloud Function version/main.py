from flask import Request, jsonify
import requests
import time
import pandas as pd
import geopy.distance
from geopy.geocoders import ArcGIS
import smtplib
from email.mime.text import MIMEText
from dateutil import parser

# URL for the data
url = "https://data.nashville.gov/resource/qywv-8sc2.json"

# Geocoding function
def geocode_address(address):
    geolocator = ArcGIS()
    location = geolocator.geocode(address)
    if location:
        return {"latitude": location.latitude, "longitude": location.longitude}
    else:
        return None

# Function to check the distance between two addresses
def check_distance(address1, address2, distance_threshold):
    coords_1 = (address1["latitude"], address1["longitude"])
    coords_2 = (address2["latitude"], address2["longitude"])
    distance = geopy.distance.distance(coords_1, coords_2).miles
    return distance <= distance_threshold

# Function to send email using SMTP library
def send_email(subject, message, to_address):
    gmail_user = "YOUR EMAIL ADDRESS HERE"
    gmail_password = "YOUR PASSWORD HERE"
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

# Flask function to handle HTTP requests
def get_data(request: Request):
    # Retrieve data from the external API
    response = requests.get(url)
    data = response.json()
    
    # Load the data into a DataFrame
    df = pd.DataFrame(data)
    
    # Set the reference address and distance threshold
    reference_address = geocode_address("YOUR ADDRESS HERE")
    distance_threshold = 1

    # Check the distance for each address in the data and send email if within distance threshold
    for index, row in df.iterrows():
        address = geocode_address(row["address"])
        if address and check_distance(reference_address, address, distance_threshold):
            call_received = parser.parse(row["call_received"])
            call_received_formatted = call_received.strftime("%m-%d-%Y %I:%M %p")
            subject = "Alert: Address within " + str(distance_threshold) + " mi"
            message = "Incident Type: " + row["incident_type"] + "\nCall Received: " + call_received_formatted + "\nAddress: " + row["address"] + "\nCity: " + row["city"]
            send_email(subject, message, "YOUR EMAIL ADDRESS HERE")
    
    # Return a JSON response
    response_data = {"message": "Data retrieved and processed successfully"}
    return jsonify(response_data)