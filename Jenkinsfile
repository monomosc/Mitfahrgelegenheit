pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python Interne_serverTest.py'
            }
        }
        stage('Deploy') {
            steps {
                sshagent (credentials: ['aa7aef04-6441-4572-ad11-380b67364795']) {
                    sh 'ssh monomo@monomo.solutions source /var/WebSrv/deployment.sh'
                }
            }
        }
    }
}