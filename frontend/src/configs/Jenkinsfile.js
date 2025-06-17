const JenkinsfileContent = `
pipeline {
    agent any

    environment {
        FLASK_API_URL = 'http://54.210.95.40:5001/scan'
        REPO_URL = 'https://github.com/YoussefElbadouri/tst'
    }

    stages {
        stage('Scan with Semgrep via Flask API') {
            steps {
                script {
                    echo "🔍 Envoi du repo à l'API Flask..."

                    def response = sh(
                        script: """
                            curl -s -X POST \${FLASK_API_URL} \\
                            -H "Content-Type: application/json" \\
                            -d '{"repo_url": "\${REPO_URL}"}'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "📋 Réponse complète :"
                    echo response

                    def parsed = readJSON text: response
                    def exitCode = parsed.exit_code
                    def status = parsed.status

                    if (exitCode.toInteger() != 0 || status == 'failed') {
                        error "🚨 Vulnérabilités détectées. Le pipeline est arrêté."
                    } else {
                        echo "✅ Aucun problème détecté. Le pipeline continue."
                    }
                }
            }
        }
    }
}
`;

export default JenkinsfileContent;