pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'python Interne_serverTest.py'
            }
        }
        stage('Deploy') {
            steps {
                echo 'deploy'
            }
        }
    }
}