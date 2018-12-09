#!/usr/bin/env python3
import os
from cwl_airflow_parser import CWLDAG, CWLJobDispatcher, CWLJobGatherer

DIR = os.path.join(os.path.dirname(os.path.abspath(os.path.join(__file__, "../"))), "cwls")

def cwl_workflow(workflow_file):
    dag = CWLDAG(cwl_workflow=workflow_file)
    dag.create()
    dag.add(CWLJobDispatcher(dag=dag), to='top')
    dag.add(CWLJobGatherer(dag=dag), to='bottom')
    return dag

dag = cwl_workflow(os.path.join(DIR, "sleep_for_an_hour_cwl_docker.cwl"))
