class user_onboarding implements Serializable {

    def steps
    def config

    user_onboarding(steps, config) {
        this.steps = steps
        this.config = config
    }

    void execute() {

        // ==============================
        // 1️⃣ Checkout Repo (users.csv)
        // ==============================
        steps.stage("Checkout SCM") {
            steps.checkout(steps.scm)
        }

        // ==============================
        // 2️⃣ Load Python Scripts
        // ==============================
        steps.stage("Load Python Scripts") {

            // Load onboarding script
            steps.libraryResource("user-onboarding.py")
                .with { content ->
                    steps.writeFile(
                        file: "user-onboarding.py",
                        text: content
                    )
                }

            // Load role setup script
            steps.libraryResource("role-setup.py")
                .with { content ->
                    steps.writeFile(
                        file: "role-setup.py",
                        text: content
                    )
                }
        }

        // ==============================
        // 3️⃣ Setup Python Environment
        // ==============================
        steps.stage("Setup Python") {
            steps.sh """
                python3 -m venv venv
                . venv/bin/activate
                pip install requests
            """
        }

        // ==============================
        // 4️⃣ Setup Roles (RBAC Automation)
        // ==============================
        steps.stage("Setup Roles") {

            steps.withCredentials([
                steps.string(
                    credentialsId: config.adminCreds,
                    variable: 'ADMIN_TOKEN'
                )
            ]) {

                steps.withEnv([
                    "JENKINS_URL=${config.jenkinsUrl}",
                    "ADMIN_USER=${config.adminUser}",
                    "ADMIN_TOKEN=${steps.env.ADMIN_TOKEN}"
                ]) {

                    steps.sh """
                        . venv/bin/activate
                        curl -s -o jenkins-cli.jar ${config.jenkinsUrl}/jnlpJars/jenkins-cli.jar
                        python role-setup.py
                    """
                }
            }
        }

        // ==============================
        // 5️⃣ Run User Onboarding
        // ==============================
        steps.stage("Run Onboarding") {

            steps.withCredentials([
                steps.string(
                    credentialsId: config.adminCreds,
                    variable: 'ADMIN_TOKEN'
                )
            ]) {

                steps.withEnv([
                    "JENKINS_URL=${config.jenkinsUrl}",
                    "ADMIN_USER=${config.adminUser}",
                    "MODE=${config.mode}",
                    "USER_EMAIL=${config.userEmail}",
                    "ROLES=${config.roles}",
                    "SEND_EMAIL=${config.sendEmail}"
                ]) {

                    steps.sh """
                        . venv/bin/activate
                        python user-onboarding.py
                    """
                }
            }
        }
    }
}
