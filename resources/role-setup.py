import jenkins.model.*
import hudson.security.*
import com.synopsys.arc.jenkins.plugins.rolestrategy.*

def instance = Jenkins.get()

def strategy = instance.getAuthorizationStrategy()

if (!(strategy instanceof RoleBasedAuthorizationStrategy)) {
    println "Role strategy not enabled!"
    return
}

def globalRoleMap = strategy.getRoleMap(RoleType.Global)
def projectRoleMap = strategy.getRoleMap(RoleType.Project)

def createRole(roleName, pattern, permissions, roleMap) {
    def role = new Role(roleName, pattern, permissions)
    if (!roleMap.getRoles().any { it.name == roleName }) {
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
