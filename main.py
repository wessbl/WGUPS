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
top_groups = []        # A list of only groups that aren't contained by another group


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
    for truck in trucks:
        print("Truck", truck.id, "has driven", round(truck.miles, 1), "miles")

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
# TODO Manage Timelies, truck limits, & package changes
# TODO HIGH SCORES: 21.4, 51.1
def dynamic_load_trucks(trucks, pkgs):
    # Create variables needed for this method
    ungrouped = []  # A list of Location ids that haven't been grouped yet
    for loc in map.locations:
        ungrouped.append(loc.id)
    group_lookup = {}       # A dictionary of all group objects, with all ids pointing to their group
    groups = []             # A list of all groups
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
                success = add_vertex(v1, v2, groups, top_groups, ungrouped, group_lookup, pkgs)
                if not success:
                    raise Exception("Encountered a deal breaker in add_vertex!")   # TODO remove

            # Added. Now check if we need to escape loops
            if len(ungrouped) == 0:
                break
        if len(ungrouped) == 0:
            break

    # Make a new array of small groups that we can remove when they become to large in next block
    small_groups = []
    smallest_size = None
    for group in top_groups:
        # Doubtful that this is needed, but will keep things more airtight
        if group.size > max_packages:
            raise Exception("Groups can only be as large as a truck can carry!")
        else:
            small_groups.append(group)
            if smallest_size is None:
                smallest_size = group.size
            else:
                smallest_size = min(group.size, smallest_size)
    # Make sure all groups in small_groups have size + smallest_size <= max_packages
    for group in small_groups:
        if group.size + smallest_size > max_packages:
            small_groups.remove(group)

    # TODO limit groups to size of truck limit
    # Create t routes (where t = number of trucks) by grouping top groups
    while True:
        # Create arrays that have the same index for corresponding data (we have to do this every loop because the
        # centers change every time groups are merged, but their length is already small and decreases by 1 every time)
        centers = []  # Holds the ids of all top_groups centers
        closest_ctr = []  # Holds closest center       closest_ctr[row][pair][vertex, distance]
        distances = []  # Holds the first distance in the closest_ctr

        # Populate centers
        for g in small_groups:
            centers.append(g.center)

        # Populate closest_ctr & distances
        for row in range(len(small_groups)):
            closest_ctr.append(map.min_dist(small_groups[row].center, centers))
            distances.append(closest_ctr[row][0][1])
            # print("Gp", small_groups[row].id, "Ctr", centers[row], ":\t", closest_ctr[row])    # Debug print

        # Find indexes for lowest distance, and the pair to the vertex with the lowest distance
        min_d = min(distances)
        # if min_d > map.avg_len:     # Only group if they're fairly close # TODO this?
        #     break
        index_1 = distances.index(min_d)
        index_2 = centers.index(closest_ctr[index_1][0][0])

        # Combine closest top groups a,b
        a = small_groups.pop(index_1)
        index_2 -= 1    # decrease to compensate for popping a off small_groups (a always comes first)
        b = small_groups.pop(index_2)
        group = combine_groups(a, b, groups)
        # Add new group to small_groups if it's still small enough to be combined
        if group.size + smallest_size <= max_packages:
            small_groups.append(group)

        # Update smallest_size
        if a.size == smallest_size or b.size == smallest_size:
            smallest_size = group.size
            for g in small_groups:
                smallest_size = min(smallest_size, g.size)
        # print("Combined groups", a.id, ",", b.id, "at distance of", min(distances))  # Debug print

        # When we've run out of small groups to combine, break loop
        if len(small_groups) < 2:
            break

    # Reorder the groups to improve mileage
    for i in range(len(top_groups)):
        top_groups[i].make_path(0, map)
        print("Gp", top_groups[i].id, "has truck", top_groups[i].truck)

    for truck in trucks:
        load_truck(truck, pkgs)


# A method that adds two vertices to a single group, or groups one vertex with another group. Will not combine groups
def add_vertex(v1, v2, groups, top_groups, ungrouped, group_lookup, pkgs):
    # TODO check for dealbreakers: adding bad truck requirement
    # TODO send delivery time & truck requirements
    deltime = None  # captures lowest delivery time in all packages
    pkgs_for_verts = pkgs.loc_dictionary[v1].copy()    # all packages for both locations
    # for pkg in pkgs.loc_dictionary[v2]:
    #     pkgs_for_verts.append(pkg)
    # for pkg_id in pkgs_for_verts:
    #     pkg = pkgs.lookup(pkg_id)
    #     if pkg.delivery_time:
    #         if deltime:
    #             if pkg.delivery_time < deltime:
    #                 deltime = pkg.delivery_time
    #         else:
    #             deltime = pkg.delivery_time

    # Add the two objects in one group
    if ungrouped.__contains__(v1):
        if ungrouped.__contains__(v2):
            # Group v1 and v2 in new group
            group = LocGroup(get_group_num())
            truck = get_truck_req(pkgs.lookup(v1), pkgs.lookup(v2))
            group.add(v1, deltime, truck)
            group.add(v2, deltime, truck)
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
            truck = get_truck_req(pkgs.lookup(v1), v2_group)
            group.add(v1, deltime, truck)
            group.add(v2_group, deltime, truck)
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
        truck = get_truck_req(v1_group, pkgs.lookup(v2))
        group.add(v2, deltime, truck)
        group.add(v1_group, deltime, truck)
        v1_group.part_of_group = group.id
        group_lookup[v2] = group
        ungrouped.remove(v2)
        groups.append(group)
        if top_groups.__contains__(v1_group):
            top_groups.remove(v1_group)
        top_groups.append(group)
    # else: Shouldn't get here, but if you do, do nothing. Use combine_groups() below

    return True


# Helper method for adding vertexes to groups
def get_top_group(group, groups):
    while group.part_of_group is not None:
        top = group.part_of_group
        group = groups[top]
    return group


# Combines 2 groups into a new group
def combine_groups(group_1, group_2, groups):
    global top_groups
    # Combine the group for v1 and v2
    if group_1 == group_2:
        return
    group = LocGroup(get_group_num())
    truck = get_truck_req(group_1, group_2)
    group.add(group_1)
    group.add(group_2)
    group.truck = truck
    groups.append(group)
    if top_groups.__contains__(group_1):
        top_groups.remove(group_1)
    if top_groups.__contains__(group_2):
        top_groups.remove(group_2)
    top_groups.append(group)
    return group


# A simple method to increment and return the group_num
def get_group_num():
    global group_num
    group_num += 1
    return group_num


# A method to get the truck requirements from 2 different entities
def get_truck_req(v1, v2):
    if v1.truck or v2.truck:
        if v1.truck:
            if v2.truck:
                if v1.truck != v2.truck:
                    raise Exception("Cannot combine groups with different trucks:", v1.truck, "and", v2.truck)
                else:
                    return v1.truck
            else:
                return v1.truck
        else:
            return v2.truck
    return None


# Loads a truck at location 0 with packages and launches it
def load_truck(truck, pkgs):
    # Add package groups with truck requirements first (delete from top_groups as you go)
    for group in top_groups:
        if group.truck and group.truck == truck.id:
            for loc in group.locs:
                for pkg in pkgs.loc_dictionary[loc]:
                    truck.packages.append(pkgs.lookup(pkg))
                    print("T", truck.id, "loaded Pkg", pkg)
                    if pkgs.lookup(pkg).truck:
                        print("Truck 2 was required!!")
            top_groups.remove(group)

    # Add package groups without truck requirements (if able)
    for group in top_groups:
        if group.size + len(truck.packages) <= max_packages:
            for loc in group.locs:
                for pkg in pkgs.loc_dictionary[loc]:
                    truck.packages.append(pkgs.lookup(pkg))
                    print("T", truck.id, "loaded Pkg", pkg)
                    if pkgs.lookup(pkg).truck:
                        print("Truck 2 was required!!")
            top_groups.remove(group)
    # Launch truck
    pkg = truck.packages[0]
    truck.drive(pkg.loc)


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

        # If truck is empty
        if len(truck.packages) == 0:
            # Go back to warehouse
            if truck.loc != 0:
                truck.drive(0)
            # Once there, reload if you can
            elif len(top_groups) > 0:
                load_truck(truck)
            else:
                truck.time = timedelta(hours=23, minutes=59, seconds=59)

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
