# cwl-airflow-parser

### About
Extends **[Apache-Airflow](https://github.com/apache/incubator-airflow)** with **[CWL v1.0](http://www.commonwl.org/v1.0/)** support.

### Installation

```sh
pip3.6 install -U cwl-airflow-parser
```

### Requirements
Package has been tested on Ubuntu 16.04.3 and Mac OS X Sierra/ High Sierra. Make sure your system satisfies the following criteria:
- python 3.6
- [docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/)
- nodejs

### Usage

```python
from cwl_airflow_parser import CWLDAG, CWLJobDispatcher, CWLJobGatherer
from datetime import timedelta

def cwl_workflow(workflow_file):
    dag = CWLDAG(default_args={
        'owner': 'airflow',
        'email': ['my@email.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 20,
        'retry_exponential_backoff': True,
        'retry_delay': timedelta(minutes=30),
        'max_retry_delay': timedelta(minutes=60 * 4)
    },
        cwl_workflow=workflow_file)
    dag.create()
    dag.add(CWLJobDispatcher(dag=dag), to='top')
    dag.add(CWLJobGatherer(dag=dag), to='bottom')

    return dag
 
cwl_workflow("/path/to/my/workflow.cwl")
```
