#! /usr/bin/env python3
import sys
import argparse
import requests
from future.moves.urllib.parse import urljoin


def get_parser():
    parser = argparse.ArgumentParser(description='DAG trigger', add_help=True)
    parser.add_argument("-d", "--dag",  help="Dag id",                          required=True)
    parser.add_argument("-r", "--run",  help="Run id",                          required=True)
    parser.add_argument("-c", "--conf", help="Configuration, json-like string", required=True)
    parser.add_argument("-u", "--url",  help="API url, with port number",       default="http://localhost:8080")
    return parser


def trigger_dag(dag_id, run_id, api_url, conf):
    return requests.post(url=urljoin(api_url, f"""/api/experimental/dags/{dag_id}/dag_runs"""),
                         json={
                             "run_id": run_id,
                             "conf": conf
                         })


def main(argsl=None):
    if argsl is None:
        argsl = sys.argv[1:]
    args,_ = get_parser().parse_known_args(argsl)
    res = trigger_dag(args.dag, args.run, args.url, args.conf)
    print(res.text)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))