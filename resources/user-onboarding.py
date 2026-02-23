import os
import csv
import requests
import secrets
import string

JENKINS_URL = os.getenv("JENKINS_URL")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
MODE = os.getenv("MODE")
USER_EMAIL = os.getenv("USER_EMAIL")
ROLES = os.getenv("ROLES")
SEND_EMAIL = os.getenv("SEND_EMAIL") == "true"

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(chars) for _ in range(12))

def create_user(username, password, email):
    url = f"{JENKINS_URL}/securityRealm/createAccountByAdmin"
    data = {
        "username": username,
        "password1": password,
        "password2": password,
        "fullname": username,
        "email": email
    }
    r = requests.post(url,
                      auth=(ADMIN_USER, ADMIN_TOKEN),
                      data=data,
                      allow_redirects=False)
    if r.status_code == 302:
        print(f"User created: {username}")
    else:
        print(f"User may already exist: {username}")

def assign_role(username, role):
    script = f'''
import jenkins.model.*
import com.michelin.cio.hudson.plugins.rolestrategy.*

def strategy = Jenkins.instance.getAuthorizationStrategy()
strategy.doAssignUserRole(
    RoleBasedAuthorizationStrategy.GLOBAL,
    "{role}",
    "{username}"
)
Jenkins.instance.save()
'''
    requests.post(f"{JENKINS_URL}/scriptText",
                  auth=(ADMIN_USER, ADMIN_TOKEN),
                  data={"script": script})

def process_user(username, email, roles):
    password = generate_password()
    create_user(username, password, email)

    for role in roles.split(","):
        assign_role(username, role.strip())

    print(f"Username: {username}")
    print(f"Roles: {roles}")
    print(f"Password: {password}")

def bulk_mode():
    with open("users.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            process_user(
                row["username"],
                row["email"],
                row["roles"]
            )

def single_mode():
    username = USER_EMAIL.split("@")[0]
    process_user(username, USER_EMAIL, ROLES)

if MODE == "bulk":
    bulk_mode()
else:
    single_mode()
