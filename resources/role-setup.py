import os
import subprocess

JENKINS_URL = os.getenv("JENKINS_URL")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

CLI_JAR = "jenkins-cli.jar"

ROLES = {
    "admin": {
        "pattern": ".*",
        "permissions": [
            "Overall/Administer"
        ]
    },
    "devops": {
        "pattern": ".*",
        "permissions": [
            "Overall/Read",
            "Job/Build",
            "Job/Cancel",
            "Job/Read",
            "Job/Configure"
        ]
    },
    "developer": {
        "pattern": ".*",
        "permissions": [
            "Overall/Read",
            "Job/Read"
        ]
    },
    "sigma": {
        "pattern": "^sigma-.*",
        "permissions": [
            "Job/Read",
            "Job/Build",
            "Job/Cancel"
        ]
    },
    "issuing": {
        "pattern": "^issuing-.*",
        "permissions": [
            "Job/Read",
            "Job/Build",
            "Job/Cancel"
        ]
    },
    "acquiring": {
        "pattern": "^acquiring-.*",
        "permissions": [
            "Job/Read",
            "Job/Build",
            "Job/Cancel"
        ]
    },
    "upi": {
        "pattern": "^upi-.*",
        "permissions": [
            "Job/Read",
            "Job/Build",
            "Job/Cancel"
        ]
    },
    "api-gw": {
        "pattern": "^api-gw-.*",
        "permissions": [
            "Job/Read",
            "Job/Build",
            "Job/Cancel"
        ]
    }
}

def run_cli(command):
    full_cmd = [
        "java", "-jar", CLI_JAR,
        "-s", JENKINS_URL,
        "-auth", f"{ADMIN_USER}:{ADMIN_TOKEN}"
    ] + command

    subprocess.run(full_cmd, check=True)

def create_roles():
    for role, data in ROLES.items():
        try:
            print(f"Creating role: {role}")
            run_cli([
                "create-role",
                "projectRoles",
                role,
                data["pattern"]
            ])
        except:
            print(f"Role {role} may already exist.")

        for perm in data["permissions"]:
            try:
                run_cli([
                    "assign-permission",
                    "projectRoles",
                    role,
                    perm
                ])
            except:
                pass

    print("All roles configured successfully.")

if __name__ == "__main__":
    create_roles()
