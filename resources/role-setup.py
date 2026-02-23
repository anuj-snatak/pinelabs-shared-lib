import os
import requests
from requests.auth import HTTPBasicAuth

# Environment Variables
JENKINS_URL = os.getenv("JENKINS_URL")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not JENKINS_URL or not ADMIN_USER or not ADMIN_TOKEN:
    print("ERROR: Missing Jenkins environment variables.")
    exit(1)

# Roles Configuration (Role Name → Job Pattern)
roles_config = {
    "admin": ".*",
    "devops": ".*",
    "developer": ".*",
    "sigma": "^sigma-.*",
    "issuing": "^issuing-.*",
    "acquiring": "^acquiring-.*",
    "upi": "^upi-.*",
    "api-gw": "^api-gw-.*"
}

# -------------------------------
# Groovy Script (Executed in Jenkins Script Console)
# -------------------------------

groovy_script = """
import jenkins.model.*
import com.synopsys.arc.jenkins.plugins.rolestrategy.*
import hudson.security.*

def jenkins = Jenkins.get()
def strategy = jenkins.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println("ERROR: Role-Based Strategy not enabled.")
    return
}

def roleMap = strategy.getRoleMap(RoleType.Project)
"""

for role, pattern in roles_config.items():
    groovy_script += f"""
if (!roleMap.getRole("{role}")) {{
    def permissions = new HashSet()
    permissions.add(hudson.model.Item.READ)
    permissions.add(hudson.model.Item.BUILD)
    permissions.add(hudson.model.Item.CANCEL)

    def newRole = new Role("{role}", "{pattern}", permissions)
    roleMap.addRole(newRole)
    println("Created role: {role}")
}} else {{
    println("Role already exists: {role}")
}}
"""

groovy_script += """
jenkins.save()
println("Role setup completed successfully.")
"""

# -------------------------------
# Execute Groovy Script via Jenkins API
# -------------------------------

try:
    response = requests.post(
        f"{JENKINS_URL}/scriptText",
        auth=HTTPBasicAuth(ADMIN_USER, ADMIN_TOKEN),
        data={"script": groovy_script},
        timeout=30
    )

    print(response.text)

except Exception as e:
    print("ERROR executing role setup:", str(e))
