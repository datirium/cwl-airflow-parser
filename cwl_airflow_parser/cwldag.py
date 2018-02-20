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


  CWLDAG creates airfow DAG where each step is CWLStepOperator
  to add steps to the top or bottom use `add` function

  add(task=Task,to='top')

 ****************************************************************************"""


import os
import json
import logging
from datetime import datetime
from six.moves import urllib

import schema_salad.schema
from cwltool.workflow import defaultMakeTool
from cwltool.errors import UnsupportedRequirement
from cwltool.resolver import tool_resolver

from airflow.models import DAG
from airflow.operators import BaseOperator
from airflow.exceptions import AirflowException

from .cwlstepoperator import CWLStepOperator
from .cwlutils import conf_get_default, shortname, load_tool


# logging.getLogger('cwltool').setLevel(conf_get_default('core', 'logging_level', 'ERROR').upper())
# logging.getLogger('salad').setLevel(conf_get_default('core', 'logging_level', 'ERROR').upper())
logging.getLogger('cwltool').setLevel(logging.ERROR)
logging.getLogger('past.translation').setLevel(logging.ERROR)
logging.getLogger('salad').setLevel(logging.ERROR)
logging.getLogger('rdflib').setLevel(logging.ERROR)

_logger = logging.getLogger(__name__)
_logger.setLevel(conf_get_default('core', 'logging_level', 'ERROR').upper())


def check_unsupported_feature(tool):
    if tool["class"] == "Workflow" and [step["id"] for step in tool["steps"] if "scatter" in step]:
        return True, "Scatter is not supported"
    return False, None


def gen_workflow_inputs(cwl_tool):
    inputs = []
    for _input in cwl_tool["inputs"]:
        custom_input = {}
        if _input.get("id", None): custom_input["id"] = shortname(_input["id"])
        if _input.get("type", None): custom_input["type"] = _input["type"]
        if _input.get("format", None): custom_input["format"] = _input["format"]
        if _input.get("doc", None): custom_input["doc"] = _input["doc"]
        if _input.get("label", None): custom_input["label"] = _input["label"]
        inputs.append(custom_input)
    return inputs


def gen_workflow_outputs(cwl_tool):
    outputs = []
    for output in cwl_tool["outputs"]:
        custom_output = {}
        if output.get("id", None): custom_output["id"] = shortname(output["id"])
        if output.get("type", None): custom_output["type"] = output["type"]
        if output.get("format", None): custom_output["format"] = output["format"]
        if output.get("doc", None): custom_output["doc"] = output["doc"]
        if output.get("label", None): custom_output["label"] = output["label"]
        if output.get("id", None): custom_output["outputSource"] = "static_step/" + shortname(output["id"])
        outputs.append(custom_output)
    return outputs


def gen_workflow_steps(cwl_file, workflow_inputs, workflow_outputs):
    return [{
        "run": cwl_file,
        "in": [{"source": workflow_input["id"], "id": workflow_input["id"]} for workflow_input in workflow_inputs],
        "out": [output["id"] for output in workflow_outputs],
        "id": "static_step"
    }]


def gen_workflow(cwl_tool, cwl_file):
    a_workflow = {
        "cwlVersion": "v1.0",
        "class": "Workflow",
        "inputs": gen_workflow_inputs(cwl_tool),
        "outputs": gen_workflow_outputs(cwl_tool)
    }
    a_workflow["steps"] = gen_workflow_steps(cwl_file, a_workflow["inputs"], a_workflow["outputs"])
    if cwl_tool.get("$namespaces", None): a_workflow["$namespaces"] = cwl_tool["$namespaces"]
    if cwl_tool.get("$schemas", None): a_workflow["$schemas"] = cwl_tool["$schemas"]
    if cwl_tool.get("requirements", None): a_workflow["requirements"] = cwl_tool["requirements"]
    return a_workflow


class CWLDAG(DAG):

    def crawl_for_tasks(self, objects):
        pass

    def __init__(
            self,
            dag_id=None,
            cwl_workflow=None,
            default_args=None,
            schedule_interval=None,
            *args, **kwargs):

        self.top_task = None
        self.bottom_task = None
        self.cwlwf = None
        self.requirements = None

        tmp_folder = conf_get_default('cwl', 'tmp_folder', '/tmp')

        _default_args = {
            'start_date': datetime.now(),
            'email_on_failure': False,
            'email_on_retry': False,
            'end_date': None,

            'tmp_folder': tmp_folder,
            'basedir': tmp_folder,

            'print_deps': False,
            'print_pre': False,
            'print_rdf': False,
            'print_dot': False,
            'relative_deps': False,
            'use_container': True,
            'rm_container': True,
            'enable_pull': True,
            'preserve_environment': ["PATH"],
            'preserve_entire_environment': False,
            'print_input_deps': False,
            'cachedir': None,
            'rm_tmpdir': True,
            'move_outputs': 'move',
            'eval_timeout': 20,
            'quiet': False,
            'version': False,
            'enable_dev': False,
            'enable_ext': False,
            'strict': False,
            'rdf_serializer': None,
            'tool_help': False,
            'pack': False,
            'on_error': 'continue',
            'relax_path_checks': False,
            'validate': False,
            'compute_checksum': True,
            'skip_schemas': True,
            'no_match_user': False,
        }

        _default_args.update(default_args if default_args else {})

        self.cwl_workflow = cwl_workflow if cwl_workflow else _default_args["cwl_workflow"]

        _dag_id = dag_id if dag_id else urllib.parse.urldefrag(self.cwl_workflow)[0].split("/")[-1] \
            .replace(".cwl", "").replace(".", "_dot_")

        super(self.__class__, self).__init__(dag_id=_dag_id,
                                             default_args=_default_args,
                                             schedule_interval=schedule_interval, *args, **kwargs)

    def create(self):
        self.cwlwf = load_tool(argsworkflow=self.cwl_workflow,
                               makeTool=defaultMakeTool,
                               resolver=tool_resolver,
                               kwargs=self.default_args,
                               strict=self.default_args['strict'])
        if type(self.cwlwf) == int or check_unsupported_feature(self.cwlwf.tool)[0]:
            raise UnsupportedRequirement(check_unsupported_feature(self.cwlwf.tool)[1])

        if self.cwlwf.tool["class"] == "CommandLineTool" or self.cwlwf.tool["class"] == "ExpressionTool":
            dirname = os.path.dirname(self.default_args["cwl_workflow"])
            filename, ext = os.path.splitext(os.path.basename(self.cwl_workflow))
            new_workflow_name = os.path.join(dirname, filename + '_workflow' + ext)
            generated_workflow = gen_workflow(self.cwlwf.tool, self.cwl_workflow)
            with open(new_workflow_name, 'w') as generated_workflow_stream:
                generated_workflow_stream.write(json.dumps(generated_workflow, indent=4))
            self.cwlwf = load_tool(argsworkflow=new_workflow_name,
                                   makeTool=defaultMakeTool,
                                   resolver=tool_resolver,
                                   strict=self.default_args['strict'])

        self.requirements = self.cwlwf.tool.get("requirements", [])

        outputs = {}

        for step in self.cwlwf.steps:
            cwl_task = CWLStepOperator(cwl_step=step,
                                       dag=self,
                                       ui_color='#5C6BC0')
            outputs[shortname(step.tool["id"])] = cwl_task

            for out in step.tool["outputs"]:
                outputs[shortname(out["id"])] = cwl_task

        for step in self.cwlwf.steps:
            current_task = outputs[shortname(step.tool["id"])]

            for inp in step.tool["inputs"]:
                step_input_sources = inp.get("source", '') \
                    if isinstance(inp.get("source", ''), list) \
                    else [inp.get("source", '')]

                for source in step_input_sources:
                    parent_task = outputs.get(shortname(source), None)
                    if parent_task and parent_task not in current_task.upstream_list:
                        current_task.set_upstream(parent_task)

        # https://material.io/guidelines/style/color.html#color-color-palette
        for t in self.tasks:
            if not t.downstream_list and t.upstream_list:
                t.ui_color = '#4527A0'
            elif not t.upstream_list:
                t.ui_color = '#303F9F'

    def add(self, task, to=None):
        if not isinstance(task, BaseOperator):
            raise AirflowException(
                "Relationships can only be set between "
                "Operators; received {}".format(task.__class__.__name__))
        if to == 'top':
            self.top_task = self.top_task if self.top_task else task
            task.set_downstream([t for t in self.tasks if t.task_id != task.task_id and not t.upstream_list])
        elif to == 'bottom':
            self.bottom_task = self.bottom_task if self.bottom_task else task
            task.set_upstream([t for t in self.tasks if t.task_id != task.task_id and not t.downstream_list])

        if self.top_task and self.bottom_task:
            self.bottom_task.reader_task_id = self.top_task.task_id
            for t in self.tasks:
                if t.task_id != self.top_task.task_id:
                    t.reader_task_id = self.top_task.task_id

    def get_output_list(self):
        outputs = {
            shortname(_output["outputSource"]): shortname(_output["id"])
            for _output in self.cwlwf.tool["outputs"]
            if _output.get("outputSource", False)
        }
        _logger.debug("{0} get_output_list: \n{1} \n {2}"
                      .format(self.dag_id, outputs, self.cwlwf.tool["outputs"]))
        return outputs
