# cwl-airflow-parser

---

## Table of Contents

* [Posting status updates](#posting-status-updates)
* [Triggering DAGs through API](#triggering-dags-through-api)
* [Check JWT signature when triggering DAG](#check-jwt-signature-when-triggering-dag)
* [Stopping DagRun](#stopping-dagrun)
* [CI with Travis](#ci-with-travis)
---

### Posting progress, task status and DagRun results

Progress, task status and DagRun results are posted to the different routes that are defined in
 `./utils/notifier.py` as
```
ROUTES = {
  "progress": "progress",
  "results":  "results",
  "status":   "status"
}
```

    Progress is posted when:
    - task finished successfully
    - dag finished successfully
    - dag failed

    Task status is posted when:
    - task started to run
    - task finished successfully
    - task failed
    - task is set to retry

    Results are posted when:
    - dag finished successfully


1. Add new Connection
    - Conn Id `process_report`
    - Conn Type `HTTP`
    - Host `localhost` or any other
    - Port `80` or any other
    - Extra `{"endpoint": "satellite/v1/"}` or any other
    
    ![Adding new connection](https://raw.githubusercontent.com/michael-kotliar/cwl-airflow-parser/master/docs/connection.png)
    
2. If JWT signature is required
    - Add Variables
        - `process_report_private_key`
        - `process_report_algorithm`
    
    ![Adding new variables](https://raw.githubusercontent.com/michael-kotliar/cwl-airflow-parser/master/docs/variables.png)

3. Test posting progress, task status and DagRun results
   ```
   python ./utils/server.py [PORT]
   ```
   Script will listen to the port `8080` (by default) on `localhost` and try to verify data with hardcoded `public_key`

4. JSON object structure
   
   Progress
   ```yaml
   {
     "payload": {
       "title":           # DagRun state. One of ["success", "running", "failed"]
       "dag_id":          # string                                   
       "run_id":          # string
       "progress":        # int from 0 to 100 percent               
       "error":           # if not "", then includes the reason of the failure as a string                 
     }
   }
   ```      
   Task status
   ```yaml
   {
     "payload": {
       "title":           # Task state. One of ["success", "running", "failed", "up_for_retry", "upstream_failed"]
       "dag_id":          # string                                   
       "run_id":          # string
       "task_id":         # string               
     }
   }
   ```   

   DagRun results
   ```yaml
   {
     "payload": {
       "dag_id":          # string                                   
       "run_id":          # string
       "results":         # JSON object to include outputs from CWL workflow               
     }
   }
   ```   

   When JWT signature is used, payload includes JWT token:
   ```yaml
   {
     "payload": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJkYWdfaWQiOiJzbGVlcF9mb3JfYW5faG91cl9jd2xfZG9ja2VyIiwicnVuX2lkIjoicnVuXzQiLCJleGVjdXRpb25fZGF0ZSI6IjIwMTgtMTItMTEgMTc6MzA6MTAiLCJzdGFydF9kYXRlIjoiMjAxOC0xMi0xMSAxNzozMDoxMCIsImVuZF9kYXRlIjpudWxsLCJzdGF0ZSI6InJ1bm5pbmciLCJ0YXNrcyI6W3sidGFza19pZCI6IkNXTEpvYkRpc3BhdGNoZXIiLCJzdGFydF9kYXRlIjoiMjAxOC0xMi0xMSAxNzozMDoxMiIsImVuZF9kYXRlIjpudWxsLCJzdGF0ZSI6InJ1bm5pbmciLCJ0cnlfbnVtYmVyIjoxLCJtYXhfdHJpZXMiOjB9LHsidGFza19pZCI6IkNXTEpvYkdhdGhlcmVyIiwic3RhcnRfZGF0ZSI6bnVsbCwiZW5kX2RhdGUiOm51bGwsInN0YXRlIjpudWxsLCJ0cnlfbnVtYmVyIjoxLCJtYXhfdHJpZXMiOjB9LHsidGFza19pZCI6InNsZWVwXzEiLCJzdGFydF9kYXRlIjpudWxsLCJlbmRfZGF0ZSI6bnVsbCwic3RhdGUiOm51bGwsInRyeV9udW1iZXIiOjEsIm1heF90cmllcyI6MH0seyJ0YXNrX2lkIjoic2xlZXBfMiIsInN0YXJ0X2RhdGUiOm51bGwsImVuZF9kYXRlIjpudWxsLCJzdGF0ZSI6bnVsbCwidHJ5X251bWJlciI6MSwibWF4X3RyaWVzIjowfSx7InRhc2tfaWQiOiJzbGVlcF8zIiwic3RhcnRfZGF0ZSI6bnVsbCwiZW5kX2RhdGUiOm51bGwsInN0YXRlIjpudWxsLCJ0cnlfbnVtYmVyIjoxLCJtYXhfdHJpZXMiOjB9LHsidGFza19pZCI6InNsZWVwXzQiLCJzdGFydF9kYXRlIjpudWxsLCJlbmRfZGF0ZSI6bnVsbCwic3RhdGUiOm51bGwsInRyeV9udW1iZXIiOjEsIm1heF90cmllcyI6MH0seyJ0YXNrX2lkIjoic2xlZXBfNSIsInN0YXJ0X2RhdGUiOm51bGwsImVuZF9kYXRlIjpudWxsLCJzdGF0ZSI6bnVsbCwidHJ5X251bWJlciI6MSwibWF4X3RyaWVzIjowfSx7InRhc2tfaWQiOiJzbGVlcF82Iiwic3RhcnRfZGF0ZSI6bnVsbCwiZW5kX2RhdGUiOm51bGwsInN0YXRlIjpudWxsLCJ0cnlfbnVtYmVyIjoxLCJtYXhfdHJpZXMiOjB9XX0.dI4TPzGyZdUkCct5EfKurJKRbQ-RXTI8NT4ZHKA47hUYep1rR8hnnGX0GsSK-UWTqGKNDHnGYAR2jVqgH0_AJVIAEZLPqBQZ_oxxddvhb-_vuwy72pCdC4mA2EYVlrdA6nNmplwEJ2u4eLAy9OKN6RuI83PIRuPrH8cXMZRjC-A"
   }
   ```


### Triggering DAGs through API
1. Run `airflow webserver`
2. Trigger DAG through API
   - Using `curl`
     Test triggering DAGs through API (set correct `DAG_ID` and `RUN_ID`)
     ```
     curl --header "Content-Type: application/json" \
          --request POST \
          --data '{"run_id":"RUN_ID","conf":"{\"job\":{\"output_folder\":\"/your/output/folder\"}}"}' \
          http://localhost:8080/api/experimental/dags/{DAG_ID}/dag_runs
     ```
   - Using `trigger.py`
     ```bash
     python ./utils/trigger.py -d DAG_ID -r RUN_ID -c "{\"job\":{\"output_folder\":\"/your/output/folder\"}}"
     ```
     
     Script will try to post JSON data to the following URL (by default)
     `http://localhost:8080/api/experimental/dags/{DAG_ID}/dag_runs`
   
     JSON data have the following structure
     ```yaml
     json_data = {
          "run_id": RUN_ID,
          "conf": "{\"job\":{\"output_folder\":\"/your/output/folder\"}}"
          "token": "jwt token"
     }
     ```
     Where `token` is generated by JWT from the object that includes only `run_id` and `conf` fields
     using hardcoded `private_key` and `RS256` algorithm (by default)
    
### Check JWT signature when triggering DAG
1. Update `airflow.cfg`
   ```
   auth_backend = cwl_airflow_parser.utils.jwt_backend
   ```
2. Add Variables
    - `jwt_backend_public_key`
    - `jwt_backend_algorithm`
3. Test trigger DAG through API (using `trigger.py`)

 
### Stopping DagRun 
1. Copy `./utils/dags/clean_dag_run.py` into the dag folder
2. Trigger `clean_dag_run` with `remove_dag_id` and `remove_run_id` parameters set in `--conf`
   ```bash
   airflow trigger_dag -r RUN_ID -c "{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}" clean_dag_run
   ```
   or
   ```bash
   curl --header "Content-Type: application/json" \
        --request POST \
        --data '{"run_id":"RUN_ID","conf":"{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}"}' \
        http://localhost:8080/api/experimental/dags/clean_dag_run/dag_runs
   ```
   or (in case using JWT singature)
   ```bash
   python3.6 ./utils/trigger.py -d clean_dag_run -r RUN_ID -c "{\"remove_dag_id\":\"some_dag_id\", \"remove_run_id\":\"some_run_id\"}"
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

### CI with Travis
1. Experimental `.travis.yml` configuration file has the following structure
   - runs two jobs separately (see `env`) with different tests to run (see `NTEST`)
   - to use `LocalExecutor` mysql-server is started in docker
   - `airflow.cfg` is updated to unpause all dags
   - `scheduler` and `webserver` are started in background
   - `cwl-airflow-tester` is run with `-s` argument to display spinner and prevent
     Travis from killing the job after being idle for more than 10 min