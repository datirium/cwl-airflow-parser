#! /usr/bin/env python3
"""
****************************************************************************

 Copyright (C) 2018 Datirium. LLC.
 All rights reserved.
 Contact: Datirium, LLC (datirium@datirium.com)

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.


 CWL utils
 File with help functions.

 ****************************************************************************"""


import jwt
import requests
import cwltool.load_tool as load
from cwltool.context import LoadingContext
from airflow.configuration import conf
from airflow.exceptions import AirflowConfigException
from airflow.models import Variable
from airflow.utils.state import State
from airflow.hooks.http_hook import HttpHook
from cwltool.load_tool import (FetcherConstructorType, resolve_tool_uri,
                               fetch_document, make_tool, validate_document)
from cwltool.resolver import tool_resolver
from cwltool.workflow import default_make_tool


def flatten(input_list):
    result = []
    for i in input_list:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)
    return result


def conf_get_default(section, key, default):
    try:
        return conf.get(section, key)
    except AirflowConfigException:
        return default


def shortname(n):
    return n.split("#")[-1]


def load_tool(argsworkflow,  # type: Union[Text, Dict[Text, Any]]
              makeTool,  # type: Callable[..., Process]
              kwargs=None,  # type: Dict
              enable_dev=False,  # type: bool
              strict=False,  # type: bool
              resolver=None,  # type: Callable[[Loader, Union[Text, Dict[Text, Any]]], Text]
              fetcher_constructor=None,  # type: FetcherConstructorType
              overrides=None
              ):
    # type: (...) -> Process
    uri, tool_file_uri = resolve_tool_uri(argsworkflow,
                                          resolver=resolver,
                                          fetcher_constructor=fetcher_constructor)

    document_loader, workflowobj, uri = fetch_document(uri, resolver=resolver,
                                                       fetcher_constructor=fetcher_constructor)

    document_loader, avsc_names, processobj, metadata, uri \
        = validate_document(document_loader, workflowobj, uri,
                            enable_dev=enable_dev,
                            strict=strict,
                            fetcher_constructor=fetcher_constructor,
                            overrides=overrides,
                            skip_schemas=kwargs.get('skip_schemas', True) if kwargs else True,
                            metadata=kwargs.get('metadata', None) if kwargs else None)
    return make_tool(document_loader, avsc_names, metadata, uri,
                     LoadingContext())


def load_cwl(cwl_file, default_args):
    load.loaders = {}
    loading_context = LoadingContext(default_args)
    loading_context.construct_tool_object = default_make_tool
    loading_context.resolver = tool_resolver
    return load.load_tool(cwl_file, loading_context)


def post_status_info(context):
    CONN_ID = "process_report"
    ROUTE = "status"
    PRIVATE_KEY = "process_report_private_key"
    ALGORITHM = "process_report_algorithm"

    try:
        # Checking connection
        http_hook = HttpHook(http_conn_id=CONN_ID)
        session = http_hook.get_conn()
        endpoint = session.headers["endpoint"]
        url = http_hook.base_url.rstrip("/") + '/' + endpoint.strip("/") + "/" + ROUTE.lstrip("/")

        # Preparing data
        dag_run = context["dag_run"]
        data_format = "%Y-%m-%d %H:%M:%S"
        data = {"dag_id": dag_run.dag_id,
                "run_id": dag_run.run_id,
                "execution_date": dag_run.execution_date.strftime(data_format) if dag_run.execution_date else None,
                "start_date": dag_run.start_date.strftime(data_format) if dag_run.start_date else None,
                "end_date": dag_run.end_date.strftime(data_format) if dag_run.end_date else None,
                "state": dag_run.state,
                "tasks": []}
        for ti in dag_run.get_task_instances():
            data["tasks"].append({"task_id": ti.task_id,
                                  "start_date": ti.start_date.strftime(data_format) if ti.start_date else None,
                                  "end_date": ti.end_date.strftime(data_format) if ti.end_date else None,
                                  "state": ti.state,
                                  "try_number": ti.try_number,
                                  "max_tries": ti.max_tries})

        # Add basic info
        data["title"] = data["state"]
        data["progress"] = int(len([task for task in data["tasks"] if task["state"] == State.SUCCESS]) / len(data["tasks"]) * 100)
        data["error"] = context["reason"] if data["state"] == State.FAILED else ""

        # Add DagRun results
        #   Results should be collected only from CWLJobGatherer class or any other class that inherits from it.
        #   Optimal solution would be to check ifinstance(ti, CWLJobGatherer), but unless code in cwlutils.py is
        #   refactored, import of CWLJobGatherer may cause LOOP.
        #   Therefore we check if isinstance(ti.xcom_pull(task_ids=ti.task_id), tuple), because only CWLJobGatherer
        #   returns tuple.
        #   Additionally, when post_status_info function is called as callback from CWLDAG, the context is equal to
        #   the context of tasks[-1], where the order of tasks depends on DB and cannot be stable.
        if dag_run.state == State.SUCCESS:
            try:
                data["results"] = [ti.xcom_pull(task_ids=ti.task_id)[0] for ti in dag_run.get_task_instances() if isinstance(ti.xcom_pull(task_ids=ti.task_id), tuple)][0]
            except Exception as ex:
                print("Failed to collect results\n", ex)

        # Try to sign data if PRIVATE_KEY and ALGORITHM are set in Variable
        try:
            data = jwt.encode(data, Variable.get(PRIVATE_KEY), algorithm=Variable.get(ALGORITHM)).decode("utf-8")
        except Exception as e:
            print("Failed to sign status data:\n", e)

        # Posting results
        prepped_request = session.prepare_request(requests.Request("POST", url, json={"payload": data}))
        http_hook.run_and_check(session, prepped_request, {})
    except Exception as e:
        print("Failed to POST status updates:\n", e)
