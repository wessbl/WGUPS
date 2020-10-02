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
max_packages = 16   # per truck
map = Map()

# * * * * *   Simulate Function   * * * * * #
# Simulates the WGUPS workday, printing package status updates between 2 given times. This function
# is the "clock" of the simulation, its only logic is to make sure the timeline is correct. Other functions are used for
# the actual algorithm
def simulate(status_time):
    print("\n\n\nStatuses at ", status_time)
    # Instantiate all variables
    trucks = []
    for i in range(num_trucks):
        trucks.append(Truck(i, truck_speed, max_packages))
    pkgs = PkgHashTable(16)
    load_pkgs(pkgs)

    # * * * * *   The Delivery Algorithm   * * * * * #
    # 1- Choose a route for x trucks
    # 2- Load the trucks, and provide a route
    # 3- Initiate simulation, keeping track of the time
    # 4- Update as needed (new packages arrive at warehouse, package updates, etc)
    get_routes(trucks, pkgs)

    # Wait for user to continue
    print("Press enter to continue...", end='')
    input()
    print("\n\n")

# The algorithm that assigns packages to trucks and plans the route
def get_routes(trucks, pkgs):
    # Get all unloaded pkg IDs
    available_pkgs = []
    for p in pkgs:
        if p.truck is None:
            available_pkgs.append(p)

    # Add one pkg to each truck until they're all loaded
    while len(available_pkgs) > 0:
        for t in trucks:
            for loc in map.min_dist(t.last_pkg_loc):
                for p in pkgs:
                    if p.loc_id == loc:
                        t.add_pkg(p)
                        available_pkgs.remove(p)
                        break
                break
            break


            break # TODO DEBUG
        break #TODO DEbug



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
          "\t3. Essential changes (# of trucks, etc)"
          "\t0. Exit")
    try:
        selection = 1  # TODO int(input())
    except:
        print("\n\n\nBad choice, try again")
        continue

    if selection == 1:
        simulate(timedelta(hours=0))
    elif selection == 2:
        print("Please input the time by hour and minute.\n"
              "Hour:\t", end='')
        hour = int(input())
        print("Minute:\t", end='')
        minute = int(input())
        simulate(timedelta(hours=hour, minutes=minute))
    elif selection == 2:
        simulate(timedelta(hours=12, minutes=3), timedelta(hours=13, minutes=12))
    else:
        continue
