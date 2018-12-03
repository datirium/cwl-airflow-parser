# cwl-airflow-parser

### Keep in mind
1. To POST status updates `http_status` connection and `http_status_endpoint`
variable should be defined in Airflow DB. They are currently hardcoded in `post_status_info`
function. Later the function should be refactored.

2. If `rsa_private_key` variable is set, RS256 encryption will be used.
   Key pair can be generated with the following commands:

   ```bash
   openssl genrsa -out private.key 2048
   openssl rsa -in private.key -outform PEM -pubout -out public.key
   ```
3. To test POST status updates, run
   ```
   python ./utils/server.py
   ```