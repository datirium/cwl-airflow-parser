# cwl-airflow-parser


### Posting status updates
1. Add new Connection
    - Conn Id `process_report`
    - Conn Type `HTTP`
    - Host `localhost` or any other
    - Port `80` or any other
    - Extra `{"endpoint": "satellite/v1/"` or any other
    
    ![Adding new connection](https://raw.githubusercontent.com/michael-kotliar/cwl-airflow-parser/master/docs/connection.png)
    
2. Enable encryption (if necessary)
    - Add Variables
        - `process_report_private_key`
        - `process_report_crypt_algorithm`
    
    ![Adding new variables](https://raw.githubusercontent.com/michael-kotliar/cwl-airflow-parser/master/docs/variables.png)

3. Test posting the status updates
   ```
   python ./utils/server.py
   ```
   Script will listen to port `80` on `localhost` and try to decrypt data with hardcoded `public_key`


### Triggering DAGs through API
##### Without encryption
1. Run `airflow webserver`
2. Test triggering DAGs through API (set correct `DAG_ID` and `RUN_ID`)
   ```
   curl --header "Content-Type: application/json" \
        --request POST \
        --data '{"run_id":"RUN_ID","conf":"{\"job\":{\"output_folder\":\"/your/output/folder\"}}"}' \
        http://localhost:8080/api/experimental/dags/{DAG_ID}/dag_runs
   ```

##### With encryption
1. Update `airflow.cfg`
   ```
   auth_backend = cwl_airflow_parser.utils.jwt_backend
   ```
2. Add Variables
    - `jwt_backend_public_key`
    - `jwt_backend_crypt_algorithm`

3. Run `airflow webserver`

4. Test triggering DAGs through API
   ```bash
   python ./utils/trigger.py -d DAG_ID -r RUN_ID -c "{\"job\":{\"output_folder\":\"/your/output/folder\"}}"
   ```
   Script will try to post JSON data to the following URL
   `http://localhost:8080/api/experimental/dags/{DAG_ID}/dag_runs` (default URL)
   
   JSON data have the following structure
   ```json
   json_data = {
        "run_id": RUN_ID,
        "conf": "{\"job\":{\"output_folder\":\"/your/output/folder\"}}"
        "check_payload": "encoded string"
   }
   ```
   Where `check_payload` is an encrypted object that includes only `run_id` and `conf` fields
   
   
### Make triggering DAGs faster (even when triggering through cli)
1. Update `airflow.cfg`
   ```bash
   api_client = airflow.api.client.json_client
   ```
   
   `json_client` will allow to trigger dag through POST to `endpoint_url` instead of parsing all the DAGs from dags folder and
    updating DB directly.
    
    Note
    - `airflow webserver` should be running
    - it won't work in combination with `auth_backend = cwl_airflow_parser.utils.jwt_backend`
 
 
### Stopping DagRun 
1. Copy `./utils/dags/clean_dag_run.py` into the dag folder
2. Trigger `clean_dag_run` with `remove_dag_id` and `remove_run_id` parameters set in `--conf`
   ```bash
   python3.6 ./utils/trigger.py -d clean_dag_run -r RUN_ID -c "{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}"
   ```
   or
   ```bash
   airflow trigger_dag -r RUN_ID -c "{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}" clean_dag_run
   ```
   
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
        