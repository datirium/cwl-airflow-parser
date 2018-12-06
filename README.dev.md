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
    