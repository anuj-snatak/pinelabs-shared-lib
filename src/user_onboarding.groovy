class user_onboarding implements Serializable {

    def steps
    def config

    user_onboarding(steps, config) {
        this.steps = steps
        this.config = config
    }

    void execute() {

        //IMPORTANT FIX
        steps.stage("Checkout SCM") {
            steps.checkout(steps.scm)
        }

        steps.stage("Load Python Script") {
            steps.libraryResource("user-onboarding.py")
                .with { content ->
                    steps.writeFile(
                        file: "user-onboarding.py",
                        text: content
                    )
                }
        }

        steps.stage("Setup Python") {
            steps.sh """
                python3 -m venv venv
                . venv/bin/activate
                pip install requests
            """
        }

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
