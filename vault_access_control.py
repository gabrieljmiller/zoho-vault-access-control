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

def get_user_id(username):
    url = 'https://vault.zoho.com/api/rest/json/v1/user'
    response = requests.get(url, headers=headers)
    data = response.json()
    
    for user in data['operation']['Details']:
        if user['username'] == username:
            return user['user_auto_id']
    return None

def get_user_ids_from_input(input_users):
    # Load alias mappings
    alias_file = 'vault_aliases.json'
    aliases = {}
    if os.path.exists(alias_file):
        with open(alias_file, 'r') as file:
            try:
                aliases = json.load(file)
            except json.JSONDecodeError:
                print("Warning: Could not decode alias file. Starting without aliases.")

    usernames = [username.strip() for username in input_users.split(",")]
    user_ids = []

    for input_name in usernames:
        # Resolve alias if it exists
        resolved_name = aliases.get(input_name, input_name)
        user_id = get_user_id(resolved_name)

        while not user_id:
            print(f"User '{input_name}' (resolved as '{resolved_name}') not found.")
            add = input(f"Would you like to add '{input_name}' as an alias? (yes/no): ").strip().lower()
            
            if add in ['yes', 'y']:
                correct_username = input(f"Enter the correct Zoho username for alias '{input_name}': ").strip()
                user_id = get_user_id(correct_username)

                while not user_id:
                    print(f"Username '{correct_username}' still not found.")
                    correct_username = input("Please enter a valid Zoho username: ").strip()
                    user_id = get_user_id(correct_username)

                add_alias(input_name, correct_username)
                resolved_name = correct_username  # for consistency
                break  # valid user_id obtained

            else:
                resolved_name = input("Enter the correct Zoho username: ").strip()
                user_id = get_user_id(resolved_name)

                while not user_id:
                    print(f"Username '{resolved_name}' still not found.")
                    resolved_name = input("Please enter a valid Zoho username: ").strip()
                    user_id = get_user_id(resolved_name)

        user_ids.append(user_id)

    return user_ids


def search_secret(secret_name):
    url = 'https://vault.zoho.com/api/rest/json/v1/secrets'

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

def access_control(approver_ids, excluded_user_ids, secret_ids):
    url = 'https://vault.zoho.com/api/rest/json/v1/accesscontrol/settings'

    # Define variables for all the data fields
    dual_approval = False  # Whether dual approval is required (True/False)
    request_timeout = "48"  # Timeout for requests (in hours)
    checkout_timeout = "30"  # Timeout for checking out passwords (in minutes)
    auto_approve = False  # Whether automatic approval is enabled (True/False)

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

def search_chambers(chamber_name):
    url = 'https://vault.zoho.com/api/rest/json/v1/chambers'
    params = {
        "isAsc": True,
        "pageNum": 0,
        "rowPerPage": 100,
        "chamberName": chamber_name
    }

    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code ==200:
        data = response.json()

        for detail in data['operation']['Details']:
            if detail['chambername'] == chamber_name:
                return detail['chamberid']
        return 'Chamber not found.'
    else:
        print(f"Error {response.status_code}: {response.text}")

def get_chamber_secrets(chamber_id):
    url = f'https://vault.zoho.com/api/rest/json/v1/chambers/{chamber_id}'
    secret_ids = []

    response = requests.get(url, headers=headers)
    
    if response.status_code ==200:
        data = response.json()

        for secret in data['operation']['Details']['chambersecrets']:
            secret_ids.append(secret['secretid'])
        return secret_ids
    else:
        print(f"Error {response.status_code}: {response.text}")

def add_alias(alias, username):
    aliases = {}
    filename = 'vault_aliases.json'

    # Load existing aliases if the file exists
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            try:
                aliases = json.load(file)
            except json.JSONDecodeError:
                print("Warning: Could not decode existing alias file. Starting fresh.")

    # Store alias -> actual username
    aliases[alias] = username

    # Write updated aliases to file
    with open(filename, 'w') as file:
        json.dump(aliases, file, indent=4)

    print(f"Alias '{alias}' saved for username '{username}' in {filename}")


secret_or_folder = input("Edit access for a secret (1) or a folder (2)?: ")

if secret_or_folder == "1":
    secret_id = search_secret(input("Enter the secret name: "))
    secret_ids = [secret_id]
elif secret_or_folder == '2':
    chamber_id = search_chambers(input("Enter the folder name: "))
    secret_ids = get_chamber_secrets(chamber_id)
else:
    print("Invalid input. Please enter 1 or 2.")
    exit()

approver_ids = get_user_ids_from_input(input("Enter the approver usernames: "))
excluded_user_ids = get_user_ids_from_input(input("Enter the excluded usernames: "))

access_control(approver_ids, excluded_user_ids, secret_ids)