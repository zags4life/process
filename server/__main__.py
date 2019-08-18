# server/__main__.py

from argparse import ArgumentParser

from ..process_mgr import ProcessManager

parser = ArgumentParser()
parser.add_argument('--port', type=int, default=5000)
args = parser.parse_args()

manager = ProcessManager(host='', port=args.port)
server = manager.get_server()
server.serve_forever()

