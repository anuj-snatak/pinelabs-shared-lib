import os
import subprocess

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

def run_cli(command):
    full_command = f"""
    java -jar jenkins-cli.jar -s {JENKINS_URL} \
    -auth {ADMIN_USER}:{ADMIN_TOKEN} {command}
    """
    subprocess.run(full_command, shell=True)

# GLOBAL ROLES
run_cli('add-role global admin -p ".*"')
run_cli('add-role global devops -p ".*"')
run_cli('add-role global developer -p ".*"')

# PROJECT ROLES
run_cli('add-role project sigma -p "^sigma-.*"')
run_cli('add-role project issuing -p "^issuing-.*"')
run_cli('add-role project acquiring -p "^acquiring-.*"')
run_cli('add-role project upi -p "^upi-.*"')
run_cli('add-role project api-gw -p "^api-gw-.*"')

print("Roles created successfully")
