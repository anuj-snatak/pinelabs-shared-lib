import requests
import os
import csv
import random
import string
import logging

# ==========================
# ENV VARIABLES
# ==========================

JENKINS_URL = os.environ.get("JENKINS_URL")
ADMIN_USER  = os.environ.get("ADMIN_USER")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

MODE       = os.environ.get("MODE")
USER_EMAIL = os.environ.get("USER_EMAIL")
ROLES      = os.environ.get("ROLES")

logging.basicConfig(level=logging.INFO)


# ==========================
# PASSWORD GENERATOR
# ==========================

def generate_password(length=14):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


# ==========================
# GET JENKINS CRUMB (CSRF)
# ==========================

def get_crumb():
    crumb_url = f"{JENKINS_URL}/crumbIssuer/api/json"
    response  = requests.get(crumb_url, auth=(ADMIN_USER, ADMIN_TOKEN))

    if response.status_code != 200:
        logging.error("Failed to retrieve crumb")
        return None, None

    data = response.json()
    return data["crumbRequestField"], data["crumb"]


# ==========================
# ✅ CHECK IF USER EXISTS
# ==========================

def user_exists(username):
    url      = f"{JENKINS_URL}/user/{username}/api/json"
    response = requests.get(url, auth=(ADMIN_USER, ADMIN_TOKEN))
    return response.status_code == 200


# ==========================
# CREATE JENKINS USER
# ==========================

def create_user(username, password):
    # ✅ Layer 2: Check against Jenkins before creating
    if user_exists(username):
        logging.warning(f"User already exists in Jenkins, skipping: {username}")
        return False

    crumb_field, crumb = get_crumb()
    url     = f"{JENKINS_URL}/securityRealm/createAccountByAdmin"
    headers = {crumb_field: crumb} if crumb else {}

    payload = {
        "username" : username,
        "password1": password,
        "password2": password,
        "fullname" : username,
        "email"    : f"{username}@pinelabs.com"
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=(ADMIN_USER, ADMIN_TOKEN)
    )

    if response.status_code in [200, 302]:
        logging.info(f"User created: {username}")
        return True
    else:
        logging.error(f"User creation failed: {response.text}")
        return False


# ==========================
# ASSIGN ROLE (ROLE STRATEGY)
# ==========================

def assign_role(username, role):
    crumb_field, crumb = get_crumb()
    url     = f"{JENKINS_URL}/role-strategy/strategy/assignRole"
    headers = {crumb_field: crumb} if crumb else {}

    payload = {
        "type"    : "globalRoles",
        "roleName": role,
        "sid"     : username
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=(ADMIN_USER, ADMIN_TOKEN)
    )

    if response.status_code in [200, 302]:
        logging.info(f"Assigned role {role} to {username}")
    else:
        logging.error(f"Role assignment failed: {response.text}")


# ==========================
# STORE PASSWORD IN JENKINS PATH
# ==========================

def store_password_in_path(username, password, role):
    base_path = "/var/lib/jenkins/user-secrets"

    try:
        os.makedirs(base_path, exist_ok=True)
        file_path = f"{base_path}/{username}.txt"

        with open(file_path, "w") as f:
            f.write(f"username: {username}\n")
            f.write(f"password: {password}\n")
            f.write(f"role: {role}\n")

        os.chmod(file_path, 0o600)
        logging.info(f"Credentials stored at: {file_path}")

    except Exception as e:
        logging.error(f"Failed to store credentials: {e}")


# ==========================
# SINGLE MODE
# ==========================

def single_mode():
    if not USER_EMAIL or not ROLES:
        logging.error("USER_EMAIL or ROLES missing")
        return

    username = USER_EMAIL.split("@")[0]

    # ✅ Duplicate check for single mode too
    if user_exists(username):
        logging.warning(f"User already exists, skipping: {username}")
        return

    password = generate_password()
    create_user(username, password)
    assign_role(username, ROLES.lower())
    store_password_in_path(username, password, ROLES.lower())
    logging.info(f"User created successfully: {username}")


# ==========================
# BULK MODE
# ==========================

def bulk_mode():
    try:
        seen_users = set()  # ✅ Layer 1: Track duplicates within CSV

        with open("users.csv") as f:
            reader = csv.DictReader(f)

            for row in reader:
                email    = row["email"]
                role     = row["roles"]
                username = email.split("@")[0]

                # ✅ Layer 1: Skip duplicate rows in CSV
                if username in seen_users:
                    logging.warning(f"Duplicate entry in CSV, skipping: {username}")
                    continue
                seen_users.add(username)

                password = generate_password()
                created  = create_user(username, password)

                if created:
                    assign_role(username, role.lower())
                    store_password_in_path(username, password, role.lower())
                    logging.info(f"User created successfully: {username}")

        logging.info("Bulk onboarding completed.")

    except FileNotFoundError:
        logging.error("users.csv not found in workspace.")


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    if MODE == "single":
        single_mode()
    elif MODE == "bulk":
        bulk_mode()
    else:
        logging.error("Invalid MODE. Use single or bulk.")
