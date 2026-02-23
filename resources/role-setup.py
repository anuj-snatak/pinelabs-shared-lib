import requests
import os
import sys

JENKINS_URL = os.environ.get("JENKINS_URL", "http://localhost:8080")
ADMIN_USER  = os.environ.get("ADMIN_USER", "admin")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    print("ERROR: ADMIN_TOKEN not set")
    sys.exit(1)

GROOVY_SCRIPT = """
import jenkins.model.*
import hudson.security.*
import com.michelin.cio.hudson.plugins.rolestrategy.RoleBasedAuthorizationStrategy
import com.michelin.cio.hudson.plugins.rolestrategy.Role
import com.synopsys.arc.jenkins.plugins.rolestrategy.RoleType
import hudson.model.Item
import hudson.model.Hudson

def instance = Jenkins.get()
def strategy = instance.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println "ERROR: Role-Based Strategy is not enabled!"
    return
}

def globalRoleMap  = strategy.getRoleMap(RoleType.Global)
def projectRoleMap = strategy.getRoleMap(RoleType.Project)

def createRole = { roleName, pattern, permissions, roleMap ->
    def role = new Role(roleName, pattern, permissions)
    if (!roleMap.getRoles().any { it.name == roleName }) {
        roleMap.addRole(role)
        println "Created role: " + roleName
    } else {
        println "Role already exists: " + roleName
    }
}

def adminPerms     = [Hudson.ADMINISTER] as Set
def devopsPerms    = [Hudson.READ, Item.READ, Item.BUILD, Item.CONFIGURE, Item.DELETE] as Set
def developerPerms = [Hudson.READ, Item.READ, Item.BUILD] as Set

createRole("admin",     ".*",            adminPerms,     globalRoleMap)
createRole("devops",    ".*",            devopsPerms,    globalRoleMap)
createRole("developer", ".*",            developerPerms, globalRoleMap)
createRole("sigma",     "^sigma-.*",     developerPerms, projectRoleMap)
createRole("issuing",   "^issuing-.*",   devopsPerms,    projectRoleMap)
createRole("acquiring", "^acquiring-.*", devopsPerms,    projectRoleMap)
createRole("upi",       "^upi-.*",       devopsPerms,    projectRoleMap)
createRole("api-gw",    "^api-gw-.*",    devopsPerms,    projectRoleMap)

instance.save()
println "Roles configured successfully"
"""

def get_crumb(session):
    resp = session.get(f"{JENKINS_URL}/crumbIssuer/api/json")
    if resp.status_code == 200:
        data = resp.json()
        return {data["crumbRequestField"]: data["crumb"]}
    return {}

def run_groovy():
    session = requests.Session()
    session.auth = (ADMIN_USER, ADMIN_TOKEN)
    crumb = get_crumb(session)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    headers.update(crumb)

    resp = session.post(
        f"{JENKINS_URL}/scriptText",
        headers=headers,
        data={"script": GROOVY_SCRIPT}
    )

    if resp.status_code == 200:
        print(resp.text)
        if "ERROR" in resp.text or "Exception" in resp.text:
            print("Groovy script reported an error.")
            sys.exit(1)
    else:
        print(f"HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    print("Setting up roles via Jenkins Script Console...")
    run_groovy()
