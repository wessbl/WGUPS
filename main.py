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

from WGUPS_Objects import Truck, Map, PkgHashTable, load_pkgs, LocGroup
from datetime import timedelta

# Define universal variables that will be needed to run a scenario
num_trucks = 2
truck_speed = 18.0
max_packages = 16  # per truck
hash_tbl_size = 16
group_num = -1
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
        trucks.append(Truck(i+1, truck_speed, max_packages))
    pkgs = PkgHashTable(16)
    load_pkgs(pkgs)

    # 1- Choose a route & load x trucks
    # greedy_load_trucks(trucks, pkgs)  # Just a method to test my classes initially
    dynamic_load_trucks(trucks, pkgs)

    # 2- Initiate simulation, keeping track of the time
    start_day(trucks, status_time)

    # Status Report
    # print("Status Report for ", pkgs.len, " packages:")
    # for pkg in pkgs:
    #     print(pkg)
    # for truck in trucks:
    #     print("Truck", truck.id, "has driven", round(truck.miles, 1), "miles")

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
            for loc_pkgs in map.min_dist(t.last_pkg_loc):           # Dict sorted by closest location (loc -> dist)
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
# TODO Manage Timelies, truck limits, Truck #, & package changes
# TODO Decide to delete this?
def dynamic_load_trucks(trucks, pkgs):
    # Create variables needed for this method
    ungrouped = []  # A list of Location ids that haven't been grouped yet
    for loc in map.locations:
        ungrouped.append(loc.id)
    group_lookup = {}       # A dictionary of all group objects, with all ids pointing to their group
    groups = []             # A list of all groups
    top_groups = []        # A list of only groups that aren't contained by another group
    num_locs = len(map.locations)

    # Sort edges by length
    edges = {}  # A dictionary that maps edge lengths to all vertex pairs with that length. edges[7.1]:[[2,1], [17,16]]
    # Traverse all distances diagonally, so that row is always greater than col
    for v1 in range(num_locs):
        if v1 == 0:    # Don't consider home vertex
            continue
        for v2 in range(v1):
            if v2 == 0:    # Don't consider home vertex
                continue
            key = map.distances[v1][v2]
            if edges.__contains__(key):
                edges[key].append([v1, v2])
            else:
                edges[key] = [[v1, v2]]
    keys = sorted(edges.keys())

    # Group shortest edges
    for length in keys:  # We won't actually visit all edges
        # Extract each vertex with this length
        vertices = edges[length]
        for vertex in vertices:
            v1 = vertex[0]
            v2 = vertex[1]

            # Add vertices to a group if one is still ungrouped
            if ungrouped.__contains__(v1) or ungrouped.__contains__(v2):
                add_vertex(v1, v2, groups, top_groups, ungrouped, group_lookup)

            # Added. Now check if we need to escape loops
            if len(ungrouped) == 0:  # Have we grouped 20% of our locations?
                break
        if len(ungrouped) == 0:  # Have we grouped 20% of our locations?
            break

    # Create t routes (where t = number of trucks) by grouping top groups
    while len(trucks) != len(top_groups):
        # Create arrays that have the same index for corresponding data (we have to do this every loop because the
        # centers change every time groups are merged, but their length is already small and decreases by 1 every time)
        centers = []  # Holds the ids of all top_groups centers
        closest_ctr = []  # Holds closest center       closest_ctr[row][pair][vertex, distance]
        distances = []  # Holds the first distance in the closest_ctr
        for group in top_groups:
            centers.append(group.center)
        for row in range(len(top_groups)):
            closest_ctr.append(map.min_dist(top_groups[row].center, centers))
            distances.append(closest_ctr[row][0][1])
            # print("Gp", top_groups[row].id, "Ctr", centers[row], ":\t", closest_ctr[row])    # Debug print
        index_1 = distances.index(min(distances))
        index_2 = centers.index(closest_ctr[index_1][0][0])
        # Combine closest top groups a,b
        a = top_groups[index_1]
        b = top_groups[index_2]
        combine_groups(a, b, groups, top_groups)
        # print("Removed groups", a.id, ",", b.id)  # Debug print

    # Reorder the groups to improve mileage
    for g in top_groups:
        g.make_path(0, map)

    # Add packages to trucks in order. A 3x nested loop seems expensive, but its actual length is equal len of pkgs
    for i in range(len(trucks)):
        for loc in top_groups[i].locs:
            for pkg in pkgs.loc_dictionary[loc]:
                trucks[i].packages.append(pkgs.lookup(pkg))


def add_vertex(v1, v2, groups, top_groups, ungrouped, group_lookup):
    if ungrouped.__contains__(v1):
        if ungrouped.__contains__(v2):
            # Group v1 and v2 in new group
            group = LocGroup(get_group_num())
            group.add(v1)
            group.add(v2)
            group_lookup[v1] = group
            group_lookup[v2] = group
            ungrouped.remove(v1)
            ungrouped.remove(v2)
            groups.append(group)
            top_groups.append(group)
        else:
            # Create new group for v1 containing v2's group
            v2_group = group_lookup[v2]
            v2_group = get_top_group(v2_group, groups)  # Only deal with top groups
            group = LocGroup(get_group_num())
            group.add(v1)
            group.add(v2_group)
            v2_group.part_of_group = group.id
            group_lookup[v1] = group
            ungrouped.remove(v1)
            groups.append(group)
            top_groups.remove(v2_group)
            top_groups.append(group)
    elif ungrouped.__contains__(v2):
        # Create new group for v1 containing v2's group
        v1_group = group_lookup[v1]
        v1_group = get_top_group(v1_group, groups)  # Only deal with top groups
        group = LocGroup(get_group_num())
        group.add(v2)
        group.add(v1_group)
        v1_group.part_of_group = group.id
        group_lookup[v2] = group
        ungrouped.remove(v2)
        groups.append(group)
        if top_groups.__contains__(v1_group):
            top_groups.remove(v1_group)
        top_groups.append(group)
    else:
        print("Used this method to combine 2 groups")


# Helper method for adding vertexes to groups
def get_top_group(group, groups):
    while group.part_of_group is not None:
        top = group.part_of_group
        group = groups[top]
    return group


# TODO delete?
# Combines 2 groups into a new group
def combine_groups(group_1, group_2, groups, top_groups):
    # Combine the group for v1 and v2
    if group_1 == group_2:
        return
    group = LocGroup(get_group_num())
    group.add(group_1)
    group.add(group_2)
    groups.append(group)
    if top_groups.__contains__(group_1):
        top_groups.remove(group_1)
    if top_groups.__contains__(group_2):
        top_groups.remove(group_2)
    top_groups.append(group)


# A simple method to increment and return the group_num
def get_group_num():
    global group_num
    group_num += 1
    return group_num


# Launches the trucks on their route, keeping track of the time as they go
def start_day(trucks, status_time):
    clock = timedelta(days=99)
    t_clock = 0     # Which truck has the earliest clock

    # Have all trucks drive, then take the min of truck times
    for truck in trucks:
        pkg = truck.packages[0]
        truck.drive(pkg.loc)
        clock = min(clock, truck.time)
        t_clock = truck.id

    # Have truck with earliest time drive to next delivery
    while clock != timedelta(days=99) and clock < status_time:
        # Deliver all packages in our truck's location
        truck = trucks[t_clock - 1]
        while truck.packages and truck.loc == truck.packages[0].loc:
            truck.unload()
        if len(truck.packages) == 0:
            # Go back to warehouse
            truck.drive(0)
            print(truck)
            truck.time = timedelta(days=99)

        # Drive
        else:
            pkg = truck.packages[0]
            truck.drive(pkg.loc)

        # Configure clock
        clock = timedelta(days=99)
        for truck in trucks:
            if truck.time < clock:
                clock = truck.time
                t_clock = truck.id

        # TODO Check for package updates (address update, or arrived at hub)


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
          "\t3. Display statuses at 12 pm"  # TODO delete
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
        simulate(timedelta(hours=23, minutes=0))
    else:
        continue
