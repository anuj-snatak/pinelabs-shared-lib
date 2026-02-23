import os
import requests
from requests.auth import HTTPBasicAuth

JENKINS_URL = os.getenv("JENKINS_URL")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

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

groovy_script = """
import jenkins.model.*
import com.michelin.cio.hudson.plugins.rolestrategy.*
import hudson.security.*

def jenkins = Jenkins.get()
def strategy = jenkins.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println("ERROR: Role-Based Strategy not enabled.")
    return
}

def roleMap = strategy.getRoleMap(RoleBasedAuthorizationStrategy.PROJECT)

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

response = requests.post(
    f"{JENKINS_URL}/scriptText",
    auth=HTTPBasicAuth(ADMIN_USER, ADMIN_TOKEN),
    data={"script": groovy_script}
)

print(response.text)
