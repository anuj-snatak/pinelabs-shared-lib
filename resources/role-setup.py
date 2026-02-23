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
    println "Role strategy not enabled! Go to Manage Jenkins > Security > Authorization and select Role-Based Strategy."
    return
}

def globalRoleMap = strategy.getRoleMap(RoleType.Global)
def projectRoleMap = strategy.getRoleMap(RoleType.Project)

// Helper function to create a role
def createRole = { roleName, pattern, permissions, roleMap ->
    def role = new Role(roleName, pattern, permissions)
    if (!roleMap.getRoles().any { it.name == roleName }) {
        roleMap.addRole(role)
        println "Created role: ${roleName}"
    } else {
        println "Role already exists: ${roleName}"
    }
}

// Define permissions
def adminPerms = [
    Hudson.ADMINISTER
] as Set

def devopsPerms = [
    Hudson.READ,
    Item.READ,
    Item.BUILD,
    Item.CONFIGURE,
    Item.DELETE
] as Set

def developerPerms = [
    Hudson.READ,
    Item.READ,
    Item.BUILD
] as Set

// Create global roles
createRole("admin",     ".*", adminPerms,     globalRoleMap)
createRole("devops",    ".*", devopsPerms,     globalRoleMap)
createRole("developer", ".*", developerPerms,  globalRoleMap)

// Create project-scoped roles
createRole("sigma",     "^sigma-.*",     developerPerms, projectRoleMap)
createRole("issuing",   "^issuing-.*",   devopsPerms,    projectRoleMap)
createRole("acquiring", "^acquiring-.*", devopsPerms,    projectRoleMap)
createRole("upi",       "^upi-.*",       devopsPerms,    projectRoleMap)
createRole("api-gw",    "^api-gw-.*",    devopsPerms,    projectRoleMap)

instance.save()
println "Roles configured successfully"
