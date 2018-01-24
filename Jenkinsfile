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
                echo 'deploy'
            }
        }
    }
}