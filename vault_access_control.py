import os
from dotenv import load_dotenv
import json
import requests

# load API key from .env
load_dotenv()

# Refresh access token
def refresh_access():
    url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {'client_id': os.getenv('CLIENT_ID'),
    'client_secret': os.getenv('CLIENT_SECRET'),
    'refresh_token': os.getenv('REFRESH_TOKEN'),
    'grant_type': 'refresh_token'}

    headers = {
    'Cookie': '_zcsr_tmp=d1de3962-273c-41e1-8d94-2178ec816d75; iamcsr=d1de3962-273c-41e1-8d94-2178ec816d75; zalb_b266a5bf57=a711b6da0e6cbadb5e254290f114a026'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    access_token = data["access_token"]

    return access_token

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Bearer {refresh_access()}'
}

def search_secret():
    url = 'https://vault.zoho.com/api/rest/json/v1/secrets'
    secret_name = input('Enter secret name: ')

    params = {
    "isAsc": True,  # Set to True for ascending order, False for descending order
    "secretName": secret_name,
    "pageNum": 0,  # Page number for pagination
    "rowPerPage": 100,  # Number of rows per page
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code ==200:
        data = response.json()

        for detail in data['operation']['Details']:
            if detail['secretname'] == secret_name:
                return detail['secretid']
        return 'Secret not found.'

    else:
        print(f"Error {response.status_code}: {response.text}")

def access_control():
    url = 'https://vault.zoho.com/api/rest/json/v1/accesscontrol/settings'

    # Define variables for all the data fields
    approver_ids = ['2022000045633067', '2022000000011003','2022000040235009']  # List of admin user auto IDs
    excluded_user_ids = ['2022000068658001', '2022000113751001']  # List of user auto IDs to be excluded from access control workflow
    dual_approval = False  # Whether dual approval is required (True/False)
    request_timeout = "48"  # Timeout for requests (in hours)
    checkout_timeout = "30"  # Timeout for checking out passwords (in minutes)
    auto_approve = False  # Whether automatic approval is enabled (True/False)
    secret_ids = [search_secret()]  # List of secret IDs to manage

    # Construct the INPUT_DATA dictionary
    input_data = {
        'admins': approver_ids,
        'users': excluded_user_ids,
        'dual_approval': dual_approval,
        'request_timeout': request_timeout,
        'checkout_timeout': checkout_timeout,
        'auto_approve': auto_approve,
        'secretids': secret_ids
    }

    # Convert the input data dictionary to a JSON string
    input_data_json = json.dumps(input_data)

    # Set up the data for the POST request (the INPUT_DATA field)
    data = {
        'INPUT_DATA': input_data_json
    }

    # make api call
    response = requests.post(url, headers=headers, data=data)

    # Print the response status code and response JSON
    if response.status_code == 200:
        print("Request was successful!")
        print(response.json())  # Print the response body (JSON)
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)  # Print the error message or failure reason


access_control()