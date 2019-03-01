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

import cwltool.load_tool as load
from cwltool.context import LoadingContext
from airflow.configuration import conf
from airflow.exceptions import AirflowConfigException
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


def load_tool(argsworkflow,              # type: Union[Text, Dict[Text, Any]]
              loadingContext             # type: LoadingContext
             ):  # type: (...) -> Process

    document_loader, workflowobj, uri = fetch_document(
        argsworkflow,
        resolver=loadingContext.resolver,
        fetcher_constructor=loadingContext.fetcher_constructor)

    document_loader, avsc_names, _, metadata, uri = validate_document(
        document_loader, workflowobj, uri,
        enable_dev=loadingContext.enable_dev,
        strict=loadingContext.strict,
        fetcher_constructor=loadingContext.fetcher_constructor,
        overrides=loadingContext.overrides_list,
        skip_schemas = True,
        metadata=loadingContext.metadata)

    return make_tool(document_loader,
                     avsc_names,
                     metadata,
                     uri,
                     loadingContext)


def load_cwl(cwl_file, default_args):
    load.loaders = {}
    loading_context = LoadingContext(default_args)
    loading_context.construct_tool_object = default_make_tool
    loading_context.resolver = tool_resolver
    tool = load_tool(cwl_file, loading_context)
    it_is_workflow = tool.tool["class"] == "Workflow"
    return tool, it_is_workflow
