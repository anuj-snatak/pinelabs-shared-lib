import requests
import json
import os
import csv
import random
import string
import logging

# ==========================
# ENV VARIABLES
# ==========================

JENKINS_URL = os.environ.get("JENKINS_URL")
ADMIN_USER = os.environ.get("ADMIN_USER")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

MODE = os.environ.get("MODE")
USER_EMAIL = os.environ.get("USER_EMAIL")
ROLES = os.environ.get("ROLES")

logging.basicConfig(level=logging.INFO)

# ==========================
# PASSWORD GENERATOR
# ==========================

def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


# ==========================
# CREATE JENKINS USER
# ==========================

def create_user(username, password):
    url = f"{JENKINS_URL}/securityRealm/createAccountByAdmin"

    payload = {
        "username": username,
        "password1": password,
        "password2": password,
        "fullname": username,
        "email": f"{username}@pinelabs.com"
    }

    response = requests.post(
        url,
        data=payload,
        auth=(ADMIN_USER, ADMIN_TOKEN)
    )

    if response.status_code in [200, 302]:
        logging.info(f"User created: {username}")
    else:
        logging.error(f"User creation failed: {response.text}")


# ==========================
# ASSIGN ROLE (ROLE STRATEGY)
# ==========================

def assign_role(username, role):
    url = f"{JENKINS_URL}/role-strategy/strategy/assignRole"

    payload = {
        "type": "globalRoles",
        "roleName": role,
        "sid": username
    }

    response = requests.post(
        url,
        data=payload,
        auth=(ADMIN_USER, ADMIN_TOKEN)
    )

    if response.status_code in [200, 302]:
        logging.info(f"Assigned role {role} to {username}")
    else:
        logging.error(f"Role assignment failed: {response.text}")


# ==========================
# STORE PASSWORD AS CREDENTIAL
# ==========================

def store_password_as_credential(username, password):
    credential_id = f"user-{username}-cred"

    url = f"{JENKINS_URL}/credentials/store/system/domain/_/createCredentials"

    payload = {
        "": "0",
        "credentials": {
            "scope": "GLOBAL",
            "id": credential_id,
            "description": f"Password for {username}",
            "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl",
            "secret": password
        }
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        url,
        auth=(ADMIN_USER, ADMIN_TOKEN),
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code in [200, 201]:
        logging.info(f"Credential stored: {credential_id}")
    else:
        logging.error(f"Credential store failed: {response.text}")


# ==========================
# SINGLE MODE
# ==========================

def single_mode():
    if not USER_EMAIL or not ROLES:
        logging.error("USER_EMAIL or ROLES missing")
        return

    username = USER_EMAIL.split("@")[0]
    password = generate_password()

    create_user(username, password)
    assign_role(username, ROLES.lower())
    store_password_as_credential(username, password)

    logging.info(f"User created successfully: {username}")
    logging.info(f"Credential ID: user-{username}-cred")


# ==========================
# BULK MODE
# ==========================

def bulk_mode():
    try:
        with open("users.csv") as f:
            reader = csv.DictReader(f)

            for row in reader:
                email = row["email"]
                role = row["roles"]

                username = email.split("@")[0]
                password = generate_password()

                create_user(username, password)
                assign_role(username, role.lower())
                store_password_as_credential(username, password)

                logging.info(f"User created successfully: {username}")
                logging.info(f"Credential ID: user-{username}-cred")

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
