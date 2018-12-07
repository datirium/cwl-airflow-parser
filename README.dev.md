# cwl-airflow-parser

### Keep in mind

1. To generate key pairs
   ```bash
   openssl genrsa -out private.key 2048
   openssl rsa -in private.key -outform PEM -pubout -out public.key
   ```
   
2. To test POST status updates
   ```
   python ./utils/server.py
   ```
   Make sure that
   - `http_status` connection id is present
   - `http_status_endpoint` variable is set
   - `rsa_private_key` variable is set (otherwise status data won't be encrypted)

3. To trigger DAG through API
   ```bash
   python ./utils/trigger.py --help
   ```
   
   Make sure that
   - `airflow webserver` is running
   - `auth_backend = cwl_airflow_parser.utils.jwt_backend` is set in `airflow.cfg`
   - `rsa_public_key` is set in variables
   
   Note
   - `rsa_public_key` is NOT the pair of `rsa_private_key` from POST
   status update section. It's paired with the private key on the client
   that triggers DAGs
   
4. To make triggering DAGs faster (even when using cli)
   
   Update `airflow.cfg` with
   ```bash
   api_client = airflow.api.client.json_client
   ```
   `json_client` will POST to `endpoint_url` instead of parsing all the DAGs from dags folder and
    updating DB directly.
    
    Make sure that
    - `airflow webserver` is running
    
    Note
    - it won't work in combination with `auth_backend = cwl_airflow_parser.utils.jwt_backend`
 
5. To completely remove DagRun

   Trigger `clean_dag_run` with `remove_dag_id` and `remove_run_id` parameters set in `--conf`
   ```bash
   python3.6 ./utils/trigger.py -d clean_dag_run -r my_run_id -c "{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}"
   ```
   
   Make sure that
   - `./utils/dags/clean_dag_run.py` is placed into dag folder
   
   Note
   - `clean_dag_run` will indicate successfull execution in case
        - `remove_dag_id` & `remove_run_id` are not found in DB
        - dagrun that corresponds to `remove_dag_id` & `remove_run_id` doen't have any tasks that
          have active PIDs
        - all active PIDs of dagrun's tasks are properly killed
   - `clean_dag_run` will indicate FAIL in case
        - after setting `Failed` state to all the tasks of the specific dagrun (defined by `remove_dag_id` & `remove_run_id`)
        we waited to long for scheduler to kill their PIDs. Timeout is equal to `2 * KILLED_TASK_CLEANUP_TIME` from
        `airflow.cfg`
   - `clean_dag_run` doesn't know if any of the tasks' PID children are stopped too 
        