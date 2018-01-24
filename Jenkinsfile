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
                sh 'ssh monomo@monomo.solutions cd /var/git/Mitfahrgelegenheit && git pull'
                sh 'ssh monomo@monomo.solutions source /var/WebSrv/deployment.sh'
            }
        }
    }
}