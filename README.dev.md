# cwl-airflow-parser

### Keep in mind
1. To POST status updates `http_status` connection and `http_status_endpoint`
variable should be defined in Airflow DB. They are currently hardcoded in `post_status_info`
function. Later the function should be refactored.
