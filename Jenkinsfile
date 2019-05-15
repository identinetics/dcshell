// pipeline tools require python3 env with jinja2, pytest and pyyaml installed

pipeline {
    agent any
    options { disableConcurrentBuilds() }

    stages {
        stage('Test1') {
            steps {
                sh '''
                    export DOCKER_REGISTRY_USER=jenkins
                    ./update_config.sh test/testenv/dc_test1.yaml.default test/testenv/dc_test1.yaml
                    export BASH_TRACE=1
                    source ./jenkins_scripts.sh
                    remove_containers alpinista && echo '.'
                    export MANIFEST_SCOPE='local'
                    export PROJ_HOME='.'
                    ./build -D $PWD -f test/testenv/dc_test1.yaml
                '''
            }
        }
    }
    post {
        always {
            sh '''
                source ./jenkins_scripts.sh
                remove_containers alpinista && echo '.'
            '''
        }
    }
}
