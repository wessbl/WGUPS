# Author:       Wesley Lancaster
# StudentID:    #001356953
# Date:         September 2020
# main.py:      Facilitates user interaction, and holds all instance data

# The Western Governors University Parcel Service (WGUPS) needs to determine the best route and delivery distribution
# for their Daily Local Deliveries. The Salt Lake City DLD route has two trucks & drivers, and an average of 40
# packages to deliver each day; each package has specific criteria and delivery requirements.
#
# This code presents a solution delivering all 40 packages, listed in the attached “WGUPS Package File,” on time,
# according to their criteria while reducing the total number of miles traveled by the trucks. The “Salt Lake City
# Downtown Map,” provides the location of each address, and the “WGUPS Distance Table” provides the distance between
# each address.
#
# The user can check the status of any given package at any given time using package IDs, including the delivery times,
# which packages are at the hub, and which are en route. The intent is to use this program for this specific location
# and to use the same program in different cities as WGUPS expands its business.

from WGUPS_Objects import Truck, Package, Location, Map, PkgHashTable, load_pkgs
from datetime import timedelta

# Define variables that will be needed to run a scenario
num_trucks = 2
truck_speed = 18.0
max_packages = 16  # per truck
hash_tbl_size = 16
map = Map()


# * * * * *   Simulate Function   * * * * * #
# Simulates the WGUPS workday, printing package status updates between 2 given times. This function
# is the "clock" of the simulation, its only logic is to make sure the timeline is correct. Other functions are used for
# the actual algorithm
def simulate(status_time):
    print("\n\n\nStatuses at ", status_time)
    if status_time == "End of Day":
        status_time = timedelta(days=99)
    # Instantiate all variables
    trucks = []
    for i in range(num_trucks):
        trucks.append(Truck(i, truck_speed, max_packages))
    pkgs = PkgHashTable(16)
    load_pkgs(pkgs)

    # * * * * *   The Delivery Algorithm   * * * * * #
    # 1- Choose a route & load x trucks
    # 2- Initiate simulation, keeping track of the time
    # 3- Update as needed (new packages arrive at warehouse, package updates, etc)
    greedy_load_trucks(trucks, pkgs)
    dynamic_load_trucks(trucks, pkgs)
    start_day(trucks, status_time)

    # Status Report
    print("Status Report for ", pkgs.len, " packages:")
    for pkg in pkgs:
        print(pkg)

    # Wait for user to continue
    print("Press enter to continue...", end='')
    input()
    print("\n\n")


# The algorithm that assigns packages to trucks and plans the route
def greedy_load_trucks(trucks, pkgs):
    # Get all unloaded pkg IDs
    available_pkgs = []
    for p_id in pkgs:
        if p_id.truck is None:
            available_pkgs.append(p_id.id)

    # BASIC GREEDY ALGORITHM: As long as trucks have room & pkgs are available, add pkgs for nearby locations
    # Does NOT account for truck limits, timeliness, or mileage
    added_to_truck = False      # Boolean value so we can switch between trucks
    while len(available_pkgs) > 0:
        for t in trucks:
            for loc_pkgs in map.min_dist(t.last_pkg_loc):           # Dict sorted by closest locatn (loc -> dist)
                for p_id in pkgs.loc_dictionary[loc_pkgs[0]]:       # Add available pkgs (loc -> {pkgs})
                    if available_pkgs.__contains__(p_id):
                        # Load pkg onto truck
                        pkg = pkgs.lookup(p_id)
                        t.add_pkg(pkg)
                        pkg.truck = t.id
                        available_pkgs.remove(p_id)
                        added_to_truck = True
                        # DEBUG print("Added pkg# ", p_id, " to truck# ", t.id, "; loc ", pkg.loc, sep='')
                if added_to_truck is True:
                    added_to_truck = False
                    break


# The dynamic algorithm that assigns packages based on location
def dynamic_load_trucks(trucks, pkgs):
    pass


# Launches the trucks on their route, keeping track of the time as they go
def start_day(trucks, status_time):
    clock = timedelta(days=99)
    t_clock = 0     # Which truck has the earliest clock

    # Have all trucks drive, then take the min of truck times
    for truck in trucks:
        pkg = truck.packages[0]
        dist = map.distances[truck.loc][pkg.loc]
        truck.drive(dist)
        clock = min(clock, truck.time)
        t_clock = truck.id

    # Have truck with earliest time drive to next delivery
    while clock != timedelta(days=99) and clock < status_time:
        # Deliver
        truck = trucks[t_clock]
        truck.unload()
        if len(truck.packages) == 0:
            # Go back to warehouse
            dist = map.distances[truck.loc][0]
            truck.drive(dist)
            print(truck)
            truck.time = timedelta(days=99)

        # Drive
        else:
            pkg = truck.packages[0]
            dist = map.distances[truck.loc][pkg.loc]
            truck.drive(dist)

        # Configure clock
        clock = timedelta(days=99)
        for truck in trucks:
            if truck.time < clock:
                clock = truck.time
                t_clock = truck.id



# TODO Check if there are (or will be?) packages not loaded on a truck
# TODO If so, plan on delivering early-ETA packages first, then fill in the time gaps with as many packages as possible


# * * * * *   Main Menu   * * * * * #
# (Project Requirement): Provide an interface for the insert and look-up functions to view the status of any
# package at any time. This function should return all information about each package, including delivery status.
#   1.  Provide screenshots to show package status of all packages at a time between 8:35 a.m. and 9:25 a.m.
#   2.  Provide screenshots to show package status of all packages at a time between 9:35 a.m. and 10:25 a.m.
#   3.  Provide screenshots to show package status of all packages at a time between 12:03 p.m. and 1:12 p.m.
selection = -1
while selection != 0:
    print("* * * WGUPS Simulator * * *\n"
          "Please make a selection:\n"
          "\t1. Run full simulation\n"
          "\t2. Show package statuses at a time\n"
          "\t3. Display statuses at 12 pm"  #TODO delete
          "\t0. Exit")
    try:
        selection = 3  # TODO int(input())
    except:
        print("\n\n\nBad choice, try again")
        continue

    if selection == 1:
        simulate("End of Day")
    elif selection == 2:
        print("Please input the time by hour and minute.\n"
              "Hour:\t", end='')
        hour = int(input())
        print("Minute:\t", end='')
        minute = int(input())
        simulate(timedelta(hours=hour, minutes=minute))
    elif selection == 3:
        simulate(timedelta(hours=12, minutes=0))
    else:
        continue
