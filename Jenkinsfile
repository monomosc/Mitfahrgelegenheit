pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'pip install -r requirements.py'
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