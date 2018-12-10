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


 CWLStepOperator is required for CWLDAG
   CWLStepOperator executes one step expects input job from previous step (xcom_pull)
   and posts output by xcom_push

 ****************************************************************************"""

import logging
import json
import os, sys, tempfile
import copy
import glob
import subprocess
import shutil
from jsonmerge import merge

from cwltool.executors import SingleJobExecutor
from cwltool.stdfsaccess import StdFsAccess
from cwltool.workflow import expression
from cwltool.context import RuntimeContext, getdefault
from cwltool.pathmapper import visit_class
from cwltool.mutation import MutationManager

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from .cwlutils import flatten, shortname, post_status_info, load_cwl

from airflow.utils.log.logging_mixin import StreamLogWriter

_logger = logging.getLogger(__name__)

class StreamLogWriterUpdated (StreamLogWriter):

    def fileno(self):
        return -1


class CWLStepOperator(BaseOperator):

    ui_color = '#3E53B7'
    ui_fgcolor = '#FFF'

    @apply_defaults
    def __init__(
            self,
            task_id=None,
            reader_task_id=None,
            ui_color=None,
            *args, **kwargs):

        self.outdir = None
        self.reader_task_id = None

        kwargs.update({"on_failure_callback": kwargs.get("on_failure_callback", post_status_info),
                       "on_retry_callback":   kwargs.get("on_retry_callback", post_status_info),
                       "on_success_callback": kwargs.get("on_success_callback", post_status_info)})

        super(self.__class__, self).__init__(task_id=task_id, *args, **kwargs)

        self.reader_task_id = reader_task_id if reader_task_id else self.reader_task_id

        if ui_color:
            self.ui_color = ui_color


    def execute(self, context):
        self.cwlwf = load_cwl(self.dag.default_args["cwl_workflow"], self.dag.default_args)
        self.cwl_step = [step for step in self.cwlwf.steps if self.task_id == step.id.split("#")[-1]][0]

        _logger.info('{0}: Running!'.format(self.task_id))
        _logger.debug('{0}: Running tool: \n{1}'.format(self.task_id,
                                                        json.dumps(self.cwl_step.embedded_tool.tool, indent=4)))

        upstream_task_ids = [t.task_id for t in self.upstream_list] + \
                            ([self.reader_task_id] if self.reader_task_id else [])
        _logger.debug('{0}: Collecting outputs from: \n{1}'.format(self.task_id,
                                                                   json.dumps(upstream_task_ids, indent=4)))

        upstream_data = self.xcom_pull(context=context, task_ids=upstream_task_ids)
        _logger.info('{0}: Upstream data: \n {1}'.format(self.task_id,
                                                         json.dumps(upstream_data, indent=4)))

        promises = {}
        for data in upstream_data:  # upstream_data is an array with { promises and outdir }
            promises = merge(promises, data["promises"])
            if "outdir" in data:
                self.outdir = data["outdir"]

        _d_args = self.dag.default_args

        if not self.outdir:
            self.outdir = _d_args['tmp_folder']

        _logger.debug('{0}: Step inputs: {1}'.format(self.task_id,
                                                     json.dumps(self.cwl_step.tool["inputs"], indent=4)))

        _logger.debug('{0}: Step outputs: {1}'.format(self.task_id,
                                                      json.dumps(self.cwl_step.tool["outputs"], indent=4)))

        jobobj = {}

        for inp in self.cwl_step.tool["inputs"]:
            jobobj_id = shortname(inp["id"]).split("/")[-1]
            source_ids = []
            promises_outputs = []
            try:
                source_ids = [shortname(source) for source in inp["source"]] \
                    if isinstance(inp["source"], list) else [shortname(inp["source"])]

                promises_outputs = [promises[source_id] for source_id in source_ids if source_id in promises]
            except:
                _logger.warning("{0}: Couldn't find source field in step input: {1}"
                                .format(self.task_id,
                                        json.dumps(inp, indent=4)))

            _logger.info('{0}: For input {1} with source_ids: {2} found upstream outputs: \n{3}'
                         .format(self.task_id,
                                 jobobj_id,
                                 source_ids,
                                 promises_outputs))

            if len(promises_outputs) > 1:
                if inp.get("linkMerge", "merge_nested") == "merge_flattened":
                    jobobj[jobobj_id] = flatten(promises_outputs)
                else:
                    jobobj[jobobj_id] = promises_outputs
            # Should also check if [None], because in this case we need to take default value
            elif len(promises_outputs) == 1 and (promises_outputs[0] is not None):
                jobobj[jobobj_id] = promises_outputs[0]
            elif "valueFrom" in inp:
                jobobj[jobobj_id] = None
            elif "default" in inp:
                d = copy.copy(inp["default"])
                jobobj[jobobj_id] = d
            else:
                continue

        _logger.debug('{0}: Collected job object: \n {1}'.format(self.task_id, json.dumps(jobobj, indent=4)))

        def _post_scatter_eval(shortio, cwl_step):
            _value_from = {
                shortname(i["id"]).split("/")[-1]:
                    i["valueFrom"] for i in cwl_step.tool["inputs"] if "valueFrom" in i
                }
            _logger.debug(
                '{0}: Step inputs with valueFrom: \n{1}'.format(self.task_id, json.dumps(_value_from, indent=4)))

            def value_from_func(k, v):
                if k in _value_from:
                    return expression.do_eval(
                        _value_from[k], shortio,
                        self.cwlwf.tool.get("requirements", []),
                        None, None, {}, context=v)
                else:
                    return v
            return {k: value_from_func(k, v) for k, v in shortio.items()}

        job = _post_scatter_eval(jobobj, self.cwl_step)
        _logger.info('{0}: Final job data: \n {1}'.format(self.task_id, json.dumps(job, indent=4)))

        _d_args['outdir'] = tempfile.mkdtemp(prefix=os.path.join(self.outdir, "step_tmp"))
        _d_args['tmpdir_prefix'] = _d_args['tmpdir_prefix'] if _d_args.get('tmpdir_prefix') else os.path.join(_d_args['outdir'], 'cwl_tmp_')
        _d_args['tmp_outdir_prefix'] = _d_args['tmp_outdir_prefix'] if _d_args.get('tmp_outdir_prefix') else os.path.join(_d_args['outdir'], 'cwl_outdir_')

        _d_args["record_container_id"] = True
        _d_args["cidfile_dir"] = self.outdir
        _d_args["cidfile_prefix"] = self.task_id

        _logger.debug(
            '{0}: Runtime context: \n {1}'.format(self, _d_args))

        executor = SingleJobExecutor()
        runtimeContext = RuntimeContext(_d_args)
        runtimeContext.make_fs_access = getdefault(runtimeContext.make_fs_access, StdFsAccess)

        for inp in self.cwl_step.tool["inputs"]:
            if inp.get("not_connected"):
                del job[shortname(inp["id"].split("/")[-1])]

        _stderr = sys.stderr
        sys.stderr = sys.__stderr__
        (output, status) = executor(self.cwl_step.embedded_tool,
                                    job,
                                    runtimeContext,
                                    logger=_logger)
        sys.stderr = _stderr

        if not output and status == "permanentFail":
            raise ValueError

        _logger.debug(
            '{0}: Embedded tool outputs: \n {1}'.format(self.task_id, json.dumps(output, indent=4)))

        promises = {}


        for out in self.cwl_step.tool["outputs"]:

            out_id = shortname(out["id"])
            jobout_id = out_id.split("/")[-1]
            try:
                promises[out_id] = output[jobout_id]
            except:
                continue

        # Unsetting the Generation from final output object
        visit_class(promises, ("File",), MutationManager().unset_generation)

        data = {"promises": promises, "outdir": self.outdir}

        _logger.info(
            '{0}: Output: \n {1}'.format(self.task_id, json.dumps(data, indent=4)))

        return data


    def on_kill(self):
        _logger.info("Stop docker containers")
        for cidfile in glob.glob(os.path.join(self.outdir, self.task_id + "*.cid")):
            try:
                with open(cidfile, "r") as inp_stream:
                    _logger.debug(f"""Read container id from {cidfile}""")
                    command = ["docker", "kill", inp_stream.read()]
                    _logger.debug(f"""Call {" ".join(command)}""")
                    p = subprocess.Popen(command, shell=False)
                    try:
                        p.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        p.kill()
            except Exception as ex:
                _logger.error(f"""Failed to stop docker container with ID from {cidfile}\n {ex}""")

        _logger.info(f"""Delete temporary output directory {self.outdir}""")
        try:
            shutil.rmtree(self.outdir)
        except Exception as ex:
            _logger.error(f"""Failed to delete temporary output directory {self.outdir}\n {ex}""")