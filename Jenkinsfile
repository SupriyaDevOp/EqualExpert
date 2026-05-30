pipeline {
    agent any

    environment {
        IMAGE_NAME   = 'equalexpert'
        IMAGE_TAG    = "build-${BUILD_NUMBER}"
        NAMESPACE    = 'equalexpert'
        KUBE_CONTEXT = 'docker-desktop'
        // Points to the patched copy — 127.0.0.1 replaced with host.docker.internal
        KUBECONFIG   = '/tmp/kube/config'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // Docker Desktop on Windows uses a random high port for the K8s API (not always 6443).
        // The mounted kubeconfig has 127.0.0.1 which is unreachable from inside the container,
        // so we copy it and swap the host while keeping the current port intact.
        stage('Patch Kubeconfig') {
            steps {
                sh """
                    mkdir -p /tmp/kube
                    sed 's|https://127.0.0.1:|https://host.docker.internal:|g' \
                        /root/.kube/config > /tmp/kube/config
                    chmod 600 /tmp/kube/config
                    kubectl config --kubeconfig=/tmp/kube/config \
                        set-cluster docker-desktop --insecure-skip-tls-verify=true
                    kubectl --context=${KUBE_CONTEXT} cluster-info
                """
            }
        }

        stage('Test') {
            steps {
                // --volumes-from shares the Jenkins container's volumes (including the workspace)
                // with the sibling container. A plain -v mount won't work here because the Docker
                // daemon is on the host and has no knowledge of paths inside the Jenkins container.
                sh """
                    docker run --rm \\
                        --volumes-from jenkins-local \\
                        -w \${WORKSPACE} \\
                        python:3.12-slim \\
                        sh -c "pip install --no-cache-dir -r requirements.txt && pytest tests/ -v --tb=short"
                """
            }
        }

        stage('Build Image') {
            steps {
                sh """
                    docker build \\
                        -t ${IMAGE_NAME}:${IMAGE_TAG} \\
                        -t ${IMAGE_NAME}:latest \\
                        .
                """
            }
        }

        stage('Deploy to Kubernetes') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                sh "kubectl --context=${KUBE_CONTEXT} apply -f deployment/namespace.yaml"
                sh "kubectl --context=${KUBE_CONTEXT} apply -f deployment/deployment.yaml"
                sh "kubectl --context=${KUBE_CONTEXT} apply -f deployment/service.yaml"
                sh "kubectl --context=${KUBE_CONTEXT} apply -f deployment/hpa.yaml"
                // rollout restart forces pods to pick up the freshly built :latest image
                sh "kubectl --context=${KUBE_CONTEXT} rollout restart deployment/equalexpert-api -n ${NAMESPACE}"
                sh "kubectl --context=${KUBE_CONTEXT} rollout status deployment/equalexpert-api -n ${NAMESPACE} --timeout=120s"
            }
        }

        stage('Smoke Test') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                // LoadBalancer is on the Windows host, not inside the Jenkins container.
                // host.docker.internal resolves to the host from within any container.
                sh """
                    for i in \$(seq 1 12); do
                        if curl -sf http://host.docker.internal/health > /dev/null 2>&1; then
                            echo 'App is up'
                            exit 0
                        fi
                        echo "Attempt \$i/12 — retrying in 5 s..."
                        sleep 5
                    done
                    echo 'Smoke test failed after 60 s'
                    exit 1
                """
            }
        }
    }

    post {
        success {
            echo "Deployment successful — http://localhost/docs (open in your browser on Windows)"
        }
        failure {
            sh "kubectl --context=${KUBE_CONTEXT} describe pods -n ${NAMESPACE} -l app=equalexpert-api || true"
            sh "kubectl --context=${KUBE_CONTEXT} logs -n ${NAMESPACE} -l app=equalexpert-api --tail=50 || true"
        }
        always {
            sh "docker image prune -f --filter 'until=24h'"
        }
    }
}
