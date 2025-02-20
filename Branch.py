import Relay_pb2_grpc
import Relay_pb2
from Relay_pb2 import Request,Response
import grpc
from multiprocessing import Lock

class Branch(Relay_pb2_grpc.BranchServicer):
    def __init__(self,id,balance,branches):
        self.id = id
        self.balance = balance
        self.branches = branches
        self.stubList = list()
        self.lock = Lock()
        self.WriteSet = list()
    def createStubs(self):
        for branch in self.branches:
            if branch != self.id:
                port = 50000 + branch
                port = str(port)
                channel = grpc.insecure_channel("localhost:" + port)
                self.stubList.append(Relay_pb2_grpc.BranchStub(channel))  
    def Deliver(self, request, context):
        if self.Check_WriteSet(request.WriteSet):
            if request.interface == "query":
                result = "Success"
                response = Response(interface = request.interface, balance = self.balance, id = request.id,result = result, branch = self.id, WriteSet = self.WriteSet)
                return(response)
            elif request.interface == "withdraw":
                self.Withdraw(request.money)
                self.Propagate_Withdraw(request)
                self.Update_Writeset()
                result = "Success"
                response = Response(interface = request.interface, balance = self.balance, id = request.id,result = result, branch = self.id, WriteSet = self.WriteSet)
                return response
            elif request.interface == "deposit":
                self.Deposit(request.money)
                self.Propagate_Deposit(request)
                self.Update_Writeset()
                result = "Success"
                response = Response(interface = request.interface, balance = self.balance, id = request.id, result = result, branch = self.id, WriteSet = self.WriteSet)
                return response
    def Cast(self, request,context):
        if self.Check_WriteSet(request.WriteSet):
            if request.interface == "withdraw":
                self.Withdraw(request.money)
                self.Update_Writeset()
                result = "Success"
                response = Response(interface = request.interface, balance = self.balance, id = request.id, result = result, branch = self.id)
                return response
            elif request.interface == "deposit":
                self.Deposit(request.money)
                self.Update_Writeset()
                result = "Success"
                response = Response(interface = request.interface, balance = self.balance, id = request.id, result = result, branch = self.id)
                return response
    def Withdraw(self,money):
        with self.lock:
            self.balance -= money
    def Deposit(self,money):
        with self.lock:
            self.balance += money
    def Update_Writeset(self):
        newEventId = len(self.WriteSet) + 1
        self.WriteSet.append(newEventId)
    def Check_WriteSet(self, ws):
        all_entries_present = True
        for entry in ws:
            if entry not in self.WriteSet:
                all_entries_present = False
            break
        return all_entries_present
        

    def Propagate_Withdraw(self,request):
        for stub in self.stubList:
            response = stub.Cast(request)
    def Propagate_Deposit(self,request):
        for stub in self.stubList:
            response = stub.Cast(request)
        