import argparse
import json
import multiprocessing
from time import sleep
from concurrent import futures
import grpc
import Relay_pb2_grpc
from Branch import Branch
from Customer import Customer

def Start_Process(process,Branch_Processes,Customer_Processes):
    branches = []
    customers = []
    branchIDs = []
    for p in process:
        if p["type"] == "branch":
            branchIDs.append(p["id"])
    for p in process:
        if p["type"] == "branch":
            branch = Branch(p["id"],p["balance"],branchIDs)
            branches.append(branch)
    print("Starting Branch Processes\n")
    for branch in branches:
        branch_process = multiprocessing.Process(target=run_branch, args=(branch,))
        Branch_Processes.append(branch_process)
        branch_process.start()
    sleep(0.25)
    for p in process:
        if p["type"] == "customer":
            customer = Customer(p["id"], p["events"])
            customers.append(customer)
    print("\nStarting Customer Processes\n")
    for customer in customers:
        customer_process = multiprocessing.Process(target=run_customer, args=(customer,))
        Customer_Processes.append(customer_process)
        customer_process.start()
    for customerProcess in Customer_Processes:
        customerProcess.join()
    sleep(1)
def run_customer(customer):
    customer.executeEvents()
    output_customer_events = json.load(open("output.json"))
    output_customer_events.extend(customer.output())
    output_customer = json.dumps(output_customer_events, indent=4)
    output_file = open("output.json", "w")
    output_file.write(output_customer)
    output_file.close()
def run_branch(branch):
    branch.createStubs()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Relay_pb2_grpc.add_BranchServicer_to_server(branch, server)
    port = 50000 + branch.id
    print("Server started. Listening on port : " + str(port))
    server.add_insecure_port("localhost:" + str(port))
    server.start()
    sleep(1.5 * branch.id)
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    try:
        print("\nNOTE: Wait till all processes are terminated.\n")
        input = json.load(open(args.input_file))
        output_file = open("output.json", "w")
        output_file.write("[]")
        output_file.close()
        Branch_Processes = []
        Customer_Processes = []
        Start_Process(input,Branch_Processes,Customer_Processes)
        print("\nTerminating all process\n")
        for p in Customer_Processes:
            p.terminate()
        for p in Branch_Processes:
            p.terminate()
    except FileNotFoundError:
        print("Could not find input file '" + args.input_file)
    except json.decoder.JSONDecodeError:
        print("Error decoding JSON file")  