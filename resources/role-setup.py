import requests
import os

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

groovy_script = """
import jenkins.model.*
import hudson.security.*
import com.synopsys.arc.jenkins.plugins.rolestrategy.*
import com.synopsys.arc.jenkins.plugins.rolestrategy.RoleType

def instance = Jenkins.getInstance()
def strategy = instance.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println "Role-Based Strategy not enabled!"
    return
}

def globalRoleMap = strategy.getRoleMap(RoleType.Global)
def projectRoleMap = strategy.getRoleMap(RoleType.Project)

def createRole(roleName, pattern, permissionsList, type) {
    def permissions = permissionsList.collect { Permission.fromId(it) }
    def role = new Role(roleName, pattern, permissions)
    def roleMap = (type == "global") ? globalRoleMap : projectRoleMap
    roleMap.addRole(role)
}

createRole("admin", ".*",
    ["hudson.model.Hudson.Administer"], "global")

createRole("devops", ".*",
    ["hudson.model.Hudson.Read",
     "hudson.model.Item.Build",
     "hudson.model.Item.Configure",
     "hudson.model.Item.Read"], "global")

createRole("developer", ".*",
    ["hudson.model.Hudson.Read",
     "hudson.model.Item.Build",
     "hudson.model.Item.Read"], "global")

createRole("sigma", "^sigma-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], "project")

createRole("issuing", "^issuing-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], "project")

createRole("acquiring", "^acquiring-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], "project")

createRole("upi", "^upi-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], "project")

createRole("api-gw", "^api-gw-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], "project")

instance.save()
println "Roles created successfully"
"""

response = requests.post(
    f"{JENKINS_URL}/scriptText",
    auth=(ADMIN_USER, ADMIN_TOKEN),
    data={"script": groovy_script}
)

print(response.text)
