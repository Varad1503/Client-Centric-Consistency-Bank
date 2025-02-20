from time import sleep

import grpc
from termcolor import colored

import Relay_pb2_grpc
from Relay_pb2 import Request


class Customer:
    def __init__(self, id, events):
        self.id = id
        self.events = events
        self.recvMsg = list()
        self.WriteSet = list()

    def executeEvents(self):
        for event in self.events:
            port = str(50000 + event["branch"])
            channel = grpc.insecure_channel("localhost:" + port)
            stub = Relay_pb2_grpc.BranchStub(channel)

            # Set MsgRequest.money = 0 for query events
            if event["interface"] == "query":
                money = 0
            else: 
                money = event["money"]

            # Send request to Branch server
            request = Request(interface = event["interface"], money = money, id = event["id"], WriteSet = self.WriteSet )
            
            response = stub.Deliver(request)
            self.WriteSet = response.WriteSet
            if event["interface"] == "query":
                print({"id" : self.id, "recv" : {"interface" : response.interface, "branch" : event["branch"], "balance" : response.balance}})
                self.recvMsg.append({"id" : self.id, "recv" : [{"interface" : response.interface, "branch" : event["branch"], "balance" : response.balance}]})
            else:
                print({"id" : self.id, "recv" : {"interface" : response.interface, "branch" : event["branch"], "result" : response.result}})
                self.recvMsg.append({"id" : self.id, "recv" : [{"interface" : response.interface, "branch" : event["branch"], "result" : response.result}]})
            sleep(0.1)
    
    def output(self):
        return self.recvMsg
          
