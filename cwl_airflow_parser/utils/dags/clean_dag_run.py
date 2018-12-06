import logging
import psutil
from airflow import configuration
from airflow.models import DAG, DagRun, DagStat, TaskInstance
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow.utils.db import provide_session
from airflow.utils.state import State
from cwl_airflow_parser.cwlutils import post_status_info


logger = logging.getLogger(__name__)


TIMEOUT = configuration.conf.getint('core', 'KILLED_TASK_CLEANUP_TIME')


@provide_session
def clean_db(dr, session=None):
    logger.debug(f"""Clean DB for {dr.dag_id} - {dr.run_id}""")
    for ti in dr.get_task_instances():
        logger.debug(f"""process {ti.dag_id} - {ti.task_id} - {ti.execution_date}""")
        ti.clear_xcom_data()
        logger.debug(" - clean Xcom table")
        session.query(TaskInstance).filter(
            TaskInstance.task_id == ti.task_id,
            TaskInstance.dag_id == ti.dag_id,
            TaskInstance.execution_date == dr.execution_date).delete(synchronize_session='fetch')
        session.commit()
        logger.debug(" - clean TaskInstance table")
    session.query(DagRun).filter(
        DagRun.dag_id == dr.dag_id,
        DagRun.run_id == dr.run_id,
    ).delete(synchronize_session='fetch')
    session.commit()
    logger.debug(" - clean dag_run table")
    DagStat.update(dr.dag_id, dirty_only=False, session=session)
    logger.debug(" - update dag_stats table")


def stop_tasks(dr):
    logger.debug(f"""Stop tasks for {dr.dag_id} - {dr.run_id}""")
    for ti in dr.get_task_instances():
        logger.debug(f"""process {ti.dag_id} - {ti.task_id} - {ti.execution_date} - {ti.pid}""")
        try:
            process = psutil.Process(ti.pid) if ti.pid else None
        except Exception:
            logger.debug(f" - cannot find process by PID {ti.pid}")
            process = None
        ti.set_state(State.FAILED)
        logger.debug(" - set state to FAILED")
        if process:
            logger.debug(f" - wait for process {ti.pid} to exit")
            process.wait(timeout=TIMEOUT * 2)  # raises psutil.TimeoutExpired if timeout. Makes task fail -> DagRun fails


def clean_dag_run(**context):
    dag_id = context['dag_run'].conf['remove_dag_id']
    run_id = context['dag_run'].conf['remove_run_id']
    dr_list = DagRun.find(dag_id=dag_id, run_id=run_id)
    for dr in dr_list:
        stop_tasks(dr)
        clean_db(dr)


dag = DAG(dag_id="clean_dag_run",
          start_date=days_ago(1),
          on_failure_callback=post_status_info,
          on_success_callback=post_status_info,
          schedule_interval=None)


run_this = PythonOperator(task_id='clean_dag_run',
                          python_callable=clean_dag_run,
                          provide_context=True,
                          dag=dag)


