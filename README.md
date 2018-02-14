# cwl-airflow-parser

### About
Extends **[Apache-Airflow](https://github.com/apache/incubator-airflow)** with **[CWL v1.0](http://www.commonwl.org/v1.0/)** support.

### Installation
1. Make sure your system satisfies the following criteria:
      - Ubuntu 16.04.3
        - python 3.6
        - pip
          ```
          sudo apt install python-pip
          pip install --upgrade pip
          ```
        - setuptools
          ```
          pip install setuptools
          ```
        - [docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/)
          ```
          sudo apt-get update
          sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
          curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
          sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
          sudo apt-get update
          sudo apt-get install docker-ce
          sudo groupadd docker
          sudo usermod -aG docker $USER
          ```
          Log out and log back in so that your group membership is re-evaluated.
        - libmysqlclient-dev
          ```bash
          sudo apt-get install libmysqlclient-dev
          ```
        - nodejs
          ```
          sudo apt-get install nodejs
          ```
