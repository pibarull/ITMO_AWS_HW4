# -*- coding: utf-8 -*-

import os
import json
import random
import datetime
import threading
from flask import Flask, render_template, Response, request


# ----------------------------------------------------------------------------------------------------------------------


class Worker:
    def __init__(self, name: str, ip_address: str):
        self.__name = name
        self.__ip_address = ip_address

    @property
    def name(self) -> str:
        return self.__name

    @property
    def ip_address(self) -> str:
        return self.__ip_address


class Task:
    def __init__(self):
        self.__locked: Worker = None
        self.__done: bool = False
        self.__identifier = random.randint(1, 9283924249)

        self.__datetime_start: datetime.datetime = None
        self.__datetime_finished: datetime.datetime = None

    @property
    def identifier(self) -> int:
        return self.__identifier

    @property
    def locked(self) -> Worker:
        return self.__locked

    @property
    def done(self) -> bool:
        return self.__done

    @property
    def datetime_start(self) -> datetime.datetime:
        return self.__datetime_start

    @property
    def datetime_finished(self) -> datetime.datetime:
        return self.__datetime_finished

    @identifier.setter
    def identifier(self, value: int):
        self.__identifier = value

    @locked.setter
    def locked(self, worker: Worker):
        self.__locked = worker

    @done.setter
    def done(self, value: bool):
        self.__done = value

    @datetime_start.setter
    def datetime_start(self, value: datetime.datetime):
        self.__datetime_start = value

    @datetime_finished.setter
    def datetime_finished(self, value: datetime.datetime):
        self.__datetime_finished = value

    def prepare_dict(self) -> {}:
        return {"identifier": self.identifier,
                "locked": {"name": self.locked.name if self.locked is not None else None,
                           "ip_address": self.locked.ip_address if self.locked is not None else None},
                "done": self.done,
                "datetime_start": self.datetime_start.strftime("%a %b %d %H:%M:%S %Y")
                if self.datetime_start is not None else None,
                "datetime_finished": self.datetime_finished.strftime("%a %b %d %H:%M:%S %Y")
                if self.datetime_finished is not None else None}

    def as_json(self) -> str:
        return json.dumps(self.prepare_dict())

    def __str__(self):
        return self.as_json()

    @staticmethod
    def from_json(dumped_json: str):
        loaded_json = json.loads(dumped_json)

        worker = Worker(loaded_json["locked"]["name"], loaded_json["locked"]["ip_address"]) \
            if (loaded_json["locked"]["name"] is not None) and (loaded_json["locked"]["ip_address"]) else None

        task = Task()
        task.locked = worker
        task.identifier = loaded_json["identifier"]
        task.done = loaded_json["done"]
        task.datetime_start = loaded_json["datetime_start"]
        task.datetime_finished = loaded_json["datetime_finished"]

        return task

def load_database(file_path: str) -> []:
    with open(file_path, "r") as f:
        data = f.readlines()

    raw_tasks_list = json.loads(data[0])

    local_tasks = []

    for raw_task in raw_tasks_list:
        local_tasks.append(Task.from_json(raw_task))

    return local_tasks


def delete_database(file_path: str):
    try:
        os.remove(file_path)

    except FileNotFoundError:
        pass


def save_database(file_path: str):
    local_tasks = []

    for task in tasks:
        local_tasks.append(task.prepare_dict())

    with open(file_path, "w") as f:
        f.write(json.dumps(local_tasks))


database_file_path = "./task.json"
tasks = []
app = Flask(__name__)

@app.route("/")
def index():
    return "Flask App!"


@app.route("/get_all_tasks/")
def get_all_tasks():
    tasks_list = []
    for i, task in enumerate(tasks):
        tasks_list.append([i+1,
                           task.identifier,
                           task.locked.name if task.locked is not None else None,
                           task.done,
                           task.datetime_start.strftime("%a %b %d %H:%M:%S %Y") if task.datetime_start is not None else None,
                           task.datetime_finished.strftime("%a %b %d %H:%M:%S %Y") if task.datetime_finished is not None else None])

    return render_template('table.html', lst=tasks_list)


@app.route('/get_all_tasks_raw/', methods=['GET'])
def get_all_tasks_raw():
    local_tasks = []

    for task in tasks:
        local_tasks.append(task.prepare_dict())

    json_response = json.dumps(local_tasks)

    response = Response(json_response, content_type='application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code = 200

    return response


@app.route('/get_task/', methods=['GET'])
def get_and_lock():
    available_task = None

    for task in tasks:
        if task.locked is None:
            available_task = task
            break

    if available_task is not None:
        request_data = json.loads(request.json)
        available_task.locked = Worker(request_data["name"], request.remote_addr)
        available_task.datetime_start = datetime.datetime.now()

        save_database(database_file_path)

        answer = available_task.prepare_dict()

    else:
        answer = None

    json_response = json.dumps(answer)

    response = Response(json_response, content_type='application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code = 200

    return response


@app.route('/finish_task/', methods=['POST'])
def finish_task():
    request_data = json.loads(request.json)

    task_identifier = request_data["identifier"]

    finished_task = None

    for task in tasks:
        if task.identifier == task_identifier:
            task.done = True
            task.datetime_finished = datetime.datetime.now()

            finished_task = task

            save_database(database_file_path)
            break

    json_response = json.dumps({"task_duration":
                                    (finished_task.datetime_finished - finished_task.datetime_start).seconds})

    response = Response(json_response, content_type='application/json; charset=utf-8')
    response.headers.add('content-length', len(json_response))
    response.status_code = 201
    return response


if __name__ == '__main__':
    delete_database(database_file_path)

    for _ in range(10):
        tasks.append(Task())

    save_database(database_file_path)

    app.run(host='0.0.0.0', port=8000)
