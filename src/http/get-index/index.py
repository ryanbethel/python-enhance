import arc
import os
import json
import time
from wasmtime import Store, Module, Instance, Linker, WasiConfig, Engine


def handler(req, context):
    stdout_path = './.stdout.txt'
    stdin_path = './.stdin.txt'
    stderr_path = './.stderr.txt'
    element_path = './elements'
    with open(stdin_path, 'w') as file:
        file.write('')
    with open(stdout_path, 'w') as file:
        file.write('')
    with open(stderr_path, 'w') as file:
        file.write('')

    store = Store()
    config = WasiConfig()
    config.stdout_file = ".stdout.txt"
    config.stdin_file = ".stdin.txt"
    config.stderr_file = ".stderr.txt"
    linker = Linker(Engine())
    linker.define_wasi()
    store = Store(linker.engine)
    store.set_wasi(config)
    module = Module.from_file(store.engine, './enhance.wasm')
    instance = linker.instantiate(store, module)

    markup = "<my-header>Hello World</my-header>"
    elements = read_elements(element_path)
    initialState = {}
    data = {"markup":markup, "elements":elements, "initialState":initialState}
    payload = json.dumps(data, indent=4)

    with open(stdin_path, 'w') as file:
        file.write(payload)

    instance.exports(store)["_start"](store)
    wait_ssr()

    with open(stdout_path, 'r') as file:
        output = file.read()


    return arc.http.res(req, {"html": output})


def wait_ssr():
    stderr_path = './.stderr.txt'
    while True:
        try:
            with open(stderr_path, 'r') as file:
                content = file.read()
                if content.strip() == "--SSR Complete--":
                    break
        except FileNotFoundError:
            print("File not found. Waiting for it to be created.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        time.sleep(1)


def read_elements(directory):
    elements = {}
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            key = os.path.splitext(filename)[0]
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                elements[key] = file.read()
    return elements


