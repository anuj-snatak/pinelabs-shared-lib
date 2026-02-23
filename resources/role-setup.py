import requests
import os

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

groovy_script = """
import jenkins.model.Jenkins

def instance = Jenkins.get()

def strategy = instance.getAuthorizationStrategy()

if (!(strategy.getClass().getName().contains("RoleBasedAuthorizationStrategy"))) {
    println "Role-Based Strategy not enabled!"
    return
}

def globalRoleMap = strategy.getRoleMap(
    com.synopsys.arc.jenkins.plugins.rolestrategy.RoleType.Global
)

def projectRoleMap = strategy.getRoleMap(
    com.synopsys.arc.jenkins.plugins.rolestrategy.RoleType.Project
)

def createRole(roleName, pattern, permissionsList, roleMap) {
    def permissions = permissionsList.collect {
        hudson.security.Permission.fromId(it)
    }

    def role = new com.synopsys.arc.jenkins.plugins.rolestrategy.Role(
        roleName,
        pattern,
        permissions
    )

    roleMap.addRole(role)
}

createRole("admin", ".*",
    ["hudson.model.Hudson.Administer"], globalRoleMap)

createRole("devops", ".*",
    ["hudson.model.Hudson.Read",
     "hudson.model.Item.Build",
     "hudson.model.Item.Configure",
     "hudson.model.Item.Read"], globalRoleMap)

createRole("developer", ".*",
    ["hudson.model.Hudson.Read",
     "hudson.model.Item.Build",
     "hudson.model.Item.Read"], globalRoleMap)

createRole("sigma", "^sigma-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], projectRoleMap)

createRole("issuing", "^issuing-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], projectRoleMap)

createRole("acquiring", "^acquiring-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], projectRoleMap)

createRole("upi", "^upi-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], projectRoleMap)

createRole("api-gw", "^api-gw-.*",
    ["hudson.model.Item.Build",
     "hudson.model.Item.Read"], projectRoleMap)

instance.save()
println "Roles created successfully"
"""

response = requests.post(
    f"{JENKINS_URL}/scriptText",
    auth=(ADMIN_USER, ADMIN_TOKEN),
    data={"script": groovy_script}
)

print(response.text)
