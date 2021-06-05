# -*- coding: utf-8 -*-

import random
import socket
import string
import json
import sympy
import requests


def get_task(server_ip: str, name: str) -> int:
    r = requests.get("http://{}:8000/get_task/".format(server_ip), json=json.dumps({"name": name}))
    task_identifier =  r.json()["identifier"]
    
    return task_identifier


def execute():
    print("Task is in progress...")
    sympy.isprime(2**2344164244-1)


def publish_answer(server_ip: str, name: str, task_identifier: int) -> int:
    r = requests.post("http://{}:8000/finish_task/".format(server_ip), json=json.dumps({"name": name,
                                                                           "identifier": task_identifier}))

    return r.json()["task_duration"]


def main():
    name: str = ""
    server_ip: str = None

    server_ip = input('Server IP: ')
    
    socket.inet_pton(socket.AF_INET, server_ip)
    charset = string.ascii_letters + string.digits

    for _ in range(10):
        name += random.choice(charset)

    task_identifier = get_task(server_ip, name)

    if task_identifier is None:
        print("No tasks to execute")

        return

    print("Task's ID - {}".format(task_identifier))
    execute()

    task_duration = publish_answer(server_ip, name, task_identifier)
    print("Task executed in {} sec".format(task_duration))


if __name__ == '__main__':
    main()
