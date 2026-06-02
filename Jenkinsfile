pipeline{
    agent any
    environment{
        KUBECONFIG='/tmp/kube/config'
        namespace='equalexpert'
        imageName='equalexpert'
    }
    stages{
        stage('scm'){
            steps{
                checkout scm
            }
        }

        stage('configure'){
            steps{
                sh """ 
                    mkdir -p /tmp/kube
                    sed 's|https://127.0.0.1:|https://host.docker.internal:|g' ~/.kube/config > /tmp/kube/config
                """
            }
        }

        stage('Build'){
            steps{
               sh """
               docker build -t ${imageName}:latest .
               """
            }
        }
        stage('Test'){
            steps{
                echo 'Testing...'
            }
        }
        stage('Deploy'){
            steps{
                sh """
                    kubectl apply -f k8s/namespace.yaml -n ${namespace}
                    kubectl apply -f k8s/deployment.yaml -n ${namespace}
                    kubectl apply -f k8s/service.yaml -n ${namespace}
                """
            }
        }
    }
}