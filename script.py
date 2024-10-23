import requests
from datetime import datetime
from io import StringIO


class StringBuilder:
    _file_str = None
    def __init__(self):
        self._file_str = StringIO()
    def Add(self, str):
        self._file_str.write(str)
    def __str__(self):
        return self._file_str.getvalue()

string_builder = StringBuilder()

# Okta Configuration
okta_domain = ''  # Replace with your Okta domain
api_token = ''  # Replace with your API token
group_ids = ['', '']  # List of the IDs of the groups to check resigned users

# Headers for Okta authentication
headers = {
    'Authorization': f'SSWS {api_token}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Function to get active user emails from ChatGPT API
def fetch_active_chatgpt_users():
    api_url = "this is a compliance API not open to public"
    api_key = "$YOUR OpenAI API KEY$"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    limit = 200  # Adjust this if needed

    users = []
    last_id = None

    while True:
        params = {"limit": limit}
        if last_id:
            params["after"] = last_id

        response = requests.get(api_url, headers=headers, params=params)
        data = response.json()

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

        # Filter only active users
        active_users = [user for user in data["data"] if user.get("status") == "active"]
        users.extend(active_users)
        last_id = data.get("last_id")
        has_more = data.get("has_more", False)

        # Debugging: Print response details
        print(f"Fetched {len(active_users)} active users on this page.")
        print(f"last_id: {last_id}, has_more: {has_more}")

        if not has_more:
            break

    # Ensure the list contains unique users
    unique_emails = list(set(user['email'] for user in users))
    return unique_emails

# Function to get user emails from multiple Okta groups and return a list
def get_user_emails_from_groups(group_ids):
    emails = []  # List to store emails from all groups
    for group_id in group_ids:
        url = f'{okta_domain}/api/v1/groups/{group_id}/users'
        while url:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    status = user.get('status')
                    if status in ['ACTIVE', 'SUSPENDED', 'PASSWORD_EXPIRED', 'RECOVERY', 'PENDING_USER_ACTION', 'STAGED', 'PROVISIONED', 'LOCKED_OUT', 'DEACTIVATED', 'DEPROVISIONED']:
                        email = user.get('profile', {}).get('email')
                        if email:
                            emails.append(email)  # Add email to the list

                # Check for next page
                links = response.links
                url = links['next']['url'] if 'next' in links else None
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break
    return list(set(emails))  # Return the list of unique emails

# Function to compare email lists and find unmatched emails
def find_unmatched_emails(list1, list2):
    return [email for email in list1 if email not in list2]

# post result to slack
def post_result():
    slack_webhook_payload = { "channel":"$YOUR CHANNEL$", "message": string_builder.__str__() }
    slack_webhook_url = '$YOUR SLACK API URL FOR SENDING MESSAGE$'
    requests.post(slack_webhook_url, json=slack_webhook_payload)
    string_builder.__init__()

def main_script():
    today = datetime.now()
    string_builder.Add(f"{today.strftime('%Y-%m-%d')} ChatGPT Disable Service\n")
    
    # Fetch active user emails from ChatGPT API
    all_emails = fetch_active_chatgpt_users()
    
    print("Total active user count from API:")
    print(len(all_emails))
    string_builder.Add("Total active user count from API: " + str(len(all_emails)) + "\n")

    # Now run the function and store its return value for multiple Okta groups
    group_emails = get_user_emails_from_groups(group_ids)

    # Find unmatched emails
    unmatched_emails = find_unmatched_emails(all_emails, group_emails)

    # Print unmatched emails
    print("Unmatched Emails:")
    string_builder.Add("Unmatched Emails:\n")
    for email in unmatched_emails:
        exception_users = ["$EXCEPTION USER$", "$EXCEPTION USER$"]
        if email not in exception_users:
            string_builder.Add(email + "\n")
            print(email)

    # Return a success status
    string_builder.Add("Successfully completed chatgpt_disable script.")
    return True

# Attempt to run the main script with retries
max_retries = 5
attempts = 0

while attempts < max_retries:
    try:
        if main_script():
            break  # Break the loop if successful
    except Exception as e:
        print(f"Attempt {attempts + 1} failed with error: {e}")
        attempts += 1
        if attempts == max_retries:
            string_builder.Add("Failed to complete chatgpt_disable script after 5 attempts.\n")

# Regardless of outcome, post the result
post_result()

# I masked off the script that deactivates users because it's not open to public yet
