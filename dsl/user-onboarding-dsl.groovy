// ==========================
// CREATE FOLDER
// ==========================

folder('Pinelabs') {
    description('Pinelabs Jenkins Automation Jobs')
    displayName('Pinelabs')
}


// ==========================
// CREATE PIPELINE JOB INSIDE FOLDER
// ==========================

pipelineJob('Pinelabs/user-onboarding') {
    displayName('Pinelabs User Onboarding')
    description('Onboard single or bulk users to Jenkins with role assignment and credential delivery')

    // ==========================
    // DO NOT RUN CONCURRENT BUILDS
    // ==========================

    concurrentBuild(false)

    // ==========================
    // PARAMETERS
    // ==========================

    parameters {
        choiceParam(
            'MODE',
            ['bulk', 'single'],
            'Select onboarding mode. Bulk reads from users.csv, Single uses the fields below.'
        )
        stringParam(
            'USER_EMAIL',
            '',
            'Required in single mode. Example: john.doe@pinelabs.com'
        )
        stringParam(
            'ROLES',
            '',
            'Comma separated roles. Example: devops,sigma. Available: admin, devops, developer, sigma, issuing, acquiring, upi, api-gw'
        )
        booleanParam(
            'SEND_EMAIL',
            true,
            'Send credentials to user email after onboarding'
        )
    }

    // ==========================
    // KEEP LAST 10 BUILDS ONLY
    // ==========================

    logRotator {
        numToKeep(10)
    }

    // ==========================
    // PIPELINE DEFINITION
    // Points to Jenkinsfile in main repo
    // ==========================

    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/anuj-snatak/pinelabs-user-onboarding.git')
                        credentials('')
                    }
                    branch('*/main')
                }
            }
            scriptPath('Jenkinsfile')
            lightweight(true)
        }
    }
}
