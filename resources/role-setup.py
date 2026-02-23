import os
import subprocess
import textwrap

JENKINS_URL = os.getenv("JENKINS_URL", "http://localhost:8080")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

groovy_script = """
import jenkins.model.*
import hudson.security.*
import com.michelin.cio.hudson.plugins.rolestrategy.*

def instance = Jenkins.get()

def strategy = instance.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println "Role strategy not enabled!"
    return
}

def globalRoleMap = strategy.getRoleMap(RoleBasedAuthorizationStrategy.GLOBAL)
def projectRoleMap = strategy.getRoleMap(RoleBasedAuthorizationStrategy.PROJECT)

def createRole(roleName, pattern, permissions, roleMap) {
    def role = new Role(roleName, pattern, permissions)
    if (!roleMap.getRoles().contains(role)) {
        roleMap.addRole(role)
        println "Created role: ${roleName}"
    } else {
        println "Role already exists: ${roleName}"
    }
}

def adminPerms = [
    Jenkins.ADMINISTER
] as Set

def devopsPerms = [
    Jenkins.READ,
    Item.READ,
    Item.BUILD,
    Item.CONFIGURE,
    Item.DELETE
] as Set

def developerPerms = [
    Jenkins.READ,
    Item.READ,
    Item.BUILD
] as Set

createRole("admin", ".*", adminPerms, globalRoleMap)
createRole("devops", ".*", devopsPerms, globalRoleMap)
createRole("developer", ".*", developerPerms, globalRoleMap)

instance.save()
println "Roles configured successfully"
"""

with open("roles.groovy", "w") as f:
    f.write(textwrap.dedent(groovy_script))

cmd = f"""
java -jar jenkins-cli.jar -s {JENKINS_URL} \
-auth {ADMIN_USER}:{ADMIN_TOKEN} groovy = < roles.groovy
"""

subprocess.run(cmd, shell=True)
