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
SEND_EMAIL = os.environ.get("SEND_EMAIL", "false").lower() == "true"

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
# CHECK IF USER EXISTS
# ==========================

def user_exists(username):
    url      = f"{JENKINS_URL}/user/{username}/api/json"
    response = requests.get(url, auth=(ADMIN_USER, ADMIN_TOKEN))
    return response.status_code == 200


# ==========================
# CREATE JENKINS USER
# ==========================

def create_user(username, password):
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
# ASSIGN ROLE
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
            f.write(f"role:     {role}\n")

        os.chmod(file_path, 0o600)
        logging.info(f"Credentials stored at: {file_path}")

    except Exception as e:
        logging.error(f"Failed to store credentials: {e}")


# ==========================
# SEND EMAIL (FUTURE USE)
# SMTP config yahan add karna hai jab ready ho
# ==========================

def send_email(to_email, username, password, roles):
    if not SEND_EMAIL:
        logging.info(f"SEND_EMAIL is false, skipping email for: {username}")
        return

    # -------------------------------------------------------
    # TODO: Uncomment and configure when SMTP is ready
    # -------------------------------------------------------
    # import smtplib
    # from email.mime.text import MIMEText
    # from email.mime.multipart import MIMEMultipart
    #
    # SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    # SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    # SMTP_USER = os.environ.get("SMTP_USER")
    # SMTP_PASS = os.environ.get("SMTP_PASS")
    #
    # msg = MIMEMultipart()
    # msg["From"]    = SMTP_USER
    # msg["To"]      = to_email
    # msg["Subject"] = "Your Jenkins Account Credentials - Pinelabs"
    #
    # body = f"""
    # Hi {username},
    #
    # Your Jenkins account has been created successfully.
    #
    # Username : {username}
    # Password : {password}
    # Roles    : {roles}
    # URL      : {JENKINS_URL}
    #
    # Please change your password after first login.
    #
    # Regards,
    # Pinelabs DevOps Team
    # """
    #
    # msg.attach(MIMEText(body, "plain"))
    #
    # try:
    #     with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    #         server.starttls()
    #         server.login(SMTP_USER, SMTP_PASS)
    #         server.sendmail(SMTP_USER, to_email, msg.as_string())
    #     logging.info(f"Email sent to: {to_email}")
    # except Exception as e:
    #     logging.error(f"Failed to send email: {e}")
    # -------------------------------------------------------

    logging.info(f"[EMAIL PLACEHOLDER] Would send credentials to: {to_email}")


# ==========================
# SINGLE MODE
# ==========================

def single_mode():
    if not USER_EMAIL or not ROLES:
        logging.error("USER_EMAIL or ROLES missing")
        return

    username = USER_EMAIL.split("@")[0]

    if user_exists(username):
        logging.warning(f"User already exists, skipping: {username}")
        return

    password  = generate_password()
    created   = create_user(username, password)

    if created:
        role_list = [r.strip().lower() for r in ROLES.split(",")]

        for role in role_list:
            assign_role(username, role)

        roles_str = ", ".join(role_list)
        store_password_in_path(username, password, roles_str)
        send_email(USER_EMAIL, username, password, roles_str)
        logging.info(f"User created successfully: {username} with roles: {role_list}")


# ==========================
# BULK MODE
# ==========================

def bulk_mode():
    try:
        seen_users = set()

        with open("users.csv") as f:
            reader = csv.DictReader(f)

            for row in reader:
                email    = row["email"]
                role     = row["roles"]
                username = email.split("@")[0]

                if username in seen_users:
                    logging.warning(f"Duplicate entry in CSV, skipping: {username}")
                    continue
                seen_users.add(username)

                password = generate_password()
                created  = create_user(username, password)

                if created:
                    assign_role(username, role.lower())
                    store_password_in_path(username, password, role.lower())
                    send_email(email, username, password, role.lower())
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
