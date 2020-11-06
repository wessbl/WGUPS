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

from WGUPS_Objects import Truck, Map, PkgHashTable, load_pkgs, LocGroup, Location
from datetime import timedelta

# Define universal variables that will be needed to run a scenario
num_trucks = 2
truck_speed = 18.0
max_packages = 16  # per truck
start_time = timedelta(hours=8)
hash_tbl_size = 16
group_num = -1
map = Map()
pkgs = PkgHashTable(1)
groups = []            # A list of all groups
top_groups = []        # A list of only groups that aren't contained by another group
trucks = []
available_locs = []     # A list of locations that have only available packages
unavailable_locs = []   # A list of locations that have an unavailable package
checkup_time = timedelta(days=99)   # A time to check on our unavailable packages


# * * * * *   Simulate Function   * * * * * #
# Simulates the WGUPS workday, printing package status updates between 2 given times. This function
# is the "clock" of the simulation, its only logic is to make sure the timeline is correct. Other functions are used for
# the actual algorithm
def simulate(status_time):
    global pkgs
    global trucks
    print("\n\n\nStatuses at ", status_time)
    if status_time == "End of Day":
        status_time = timedelta(days=99)
    # Instantiate all variables
    trucks = []
    for i in range(num_trucks):
        trucks.append(Truck(i+1, truck_speed, max_packages, start_time))
    pkgs = PkgHashTable(16)
    load_pkgs(pkgs)

    # Get all of the cluster to hold the same data
    cluster = None
    ready_at = None
    for pkg in pkgs:
        cluster = manage_clusters(pkg)
        if pkg.ready_at:
            if not ready_at:
                ready_at = pkg.ready_at
            else:
                ready_at = max(ready_at, pkg.ready_at)
    if cluster:
        for pkg in cluster:
            pkg = pkgs.lookup(pkg)
            pkg.cluster = cluster
            if ready_at:
                pkg.ready_at = ready_at
                map.locations[pkg.loc].ready_at = ready_at

    # 1- Group locations and load trucks with their packages
    dynamic_group_locs(start_time)
    for truck in trucks:
        create_route(truck)

    # 2- Initiate simulation, keeping track of the time
    start_day(status_time)

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


# A recursive algorithm that manages package clusters
def manage_clusters(given, cluster=None, visited=None):
    # If this package's cluster is None
    if not given.cluster:
        # If this package's cluster is empty, set it to the given cluster with its ID
        if not cluster:
            return
        elif not cluster.__contains__(given.id):
            cluster.append(given.id)
            given.cluster = cluster
            return cluster

    if not visited:
        visited = []
        cluster = []
    visited.append(given.id)

    if not cluster.__contains__(given.id):
        cluster.append(given.id)

    # Recursively visit all in the cluster
    for pkg in given.cluster:
        if not visited.__contains__(pkg):
            pkg = pkgs.lookup(pkg)
            new_cluster = manage_clusters(pkg, cluster, visited)
            for p in new_cluster:
                if not cluster.__contains__(p):
                    cluster.append(p)
    given.cluster = cluster
    return cluster


# The algorithm that assigns packages to trucks and plans the route
def greedy_load_trucks():
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
# TODO Manage package groups and package changes
# TODO HIGH SCORES: 44.8, 59.8
def dynamic_group_locs(time):
    # Create variables needed for this method
    check_pkg_availability(time)
    ungrouped = available_locs.copy()  # A list of Location ids that haven't been grouped yet
    group_lookup = {}       # A dictionary of all group objects, with all ids pointing to their group
    num_locs = len(ungrouped)

    # Sort edges by length
    edges = {}  # A dictionary that maps edge lengths to all vertex pairs with that length. edges[7.1]:[[2,1], [17,16]]
    # Traverse all distances diagonally, so that row is always greater than col
    for v1 in ungrouped:
        for v2 in ungrouped:
            if v2 == v1:
                break
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
                create_group(v1, v2, ungrouped, group_lookup)

            # Added. Now check if we need to escape loops
            if len(ungrouped) == 0:
                break
        if len(ungrouped) == 0:
            break

    # Make a new array of small groups that we can remove when they become too large in next block
    small_groups = []
    smallest_size = None    # The group with the smallest size (to help us know when to eliminate a large group)
    for group in top_groups:
        small_groups.append(group)
        if smallest_size is None:
            smallest_size = group.pkg_size
        else:
            smallest_size = min(group.pkg_size, smallest_size)
    # Make sure all groups in small_groups have size + smallest_size <= max_packages
    for group in small_groups:
        if group.pkg_size + smallest_size > max_packages:
            small_groups.remove(group)

    # Combine groups when able
    while len(small_groups) > 1:
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
        index_1 = distances.index(min_d)
        index_2 = centers.index(closest_ctr[index_1][0][0])

        # Get closest top groups a,b
        a = small_groups.pop(index_1)
        index_2 -= 1    # decrease to compensate for popping a off small_groups (a always comes first)
        b = small_groups.pop(index_2)

        # If the groups are not combinable (pkg_size limit or truck requirements), add back in the smaller group
        if a.pkg_size + b.pkg_size > max_packages:
            if a.pkg_size > b.pkg_size:
                small_groups.append(b)
                continue
            else:
                small_groups.append(a)
                continue

        # If the groups have an unmatched truck requirement, add one back in. Otherwise, group them
        if a.truck != b.truck:
            if a.truck:
                small_groups.append(b)
                continue
            else:
                small_groups.append(a)
                continue
        else:
            group = create_group(a, b)

            # Add new group to small_groups if it's still small enough to be combined
            if group.pkg_size + smallest_size <= max_packages:
                small_groups.append(group)

            # Update smallest_size
            if a.pkg_size == smallest_size or b.pkg_size == smallest_size:
                smallest_size = group.pkg_size
                for g in small_groups:
                    smallest_size = min(smallest_size, g.pkg_size)
            # print("Combined groups", a.id, ",", b.id, "at distance of", min(distances))  # Debug print


# A method that adds two locations to a single group, or groups one vertex with another group. Combines groups, do not
# use on a loop!
def create_group(l1, l2, ungrouped=[], group_lookup=None):
    # TODO check for dealbreakers: adding bad truck requirement

    # Add the two objects in one group
    if ungrouped.__contains__(l1):

        # Group v1 and v2 in new group
        if ungrouped.__contains__(l2):
            group = LocGroup(get_group_num())
            loc1 = map.locations[l1]
            loc2 = map.locations[l2]
            truck = get_truck_req(loc1, loc2)
            group.add(l1, len(pkgs.loc_dictionary[l1]), truck, loc1.deltime)
            group.add(l2, len(pkgs.loc_dictionary[l2]), truck, loc2.deltime)
            group_lookup[l1] = group
            group_lookup[l2] = group
            ungrouped.remove(l1)
            ungrouped.remove(l2)
            groups.append(group)
            top_groups.append(group)

        # Create new group for v1 containing v2's group
        else:
            v2_group = group_lookup[l2]
            v2_group = get_top_group(v2_group)  # Only deal with top groups
            group = LocGroup(get_group_num())
            loc1 = map.locations[l1]
            truck = get_truck_req(loc1, v2_group)
            group.add(l1, len(pkgs.loc_dictionary[l1]), truck, loc1.deltime)
            group.add(v2_group, v2_group.pkg_size, truck, v2_group.deltime)
            v2_group.part_of_group = group.id
            group_lookup[l1] = group
            ungrouped.remove(l1)
            groups.append(group)
            top_groups.remove(v2_group)
            top_groups.append(group)

    # Create new group for v1 containing v2's group
    elif ungrouped.__contains__(l2):
        v1_group = group_lookup[l1]
        v1_group = get_top_group(v1_group)  # Only deal with top groups
        group = LocGroup(get_group_num())
        loc2 = map.locations[l2]
        truck = get_truck_req(v1_group, loc2)
        group.add(l2, len(pkgs.loc_dictionary[l2]), truck, loc2.deltime)
        group.add(v1_group, v1_group.pkg_size, truck, v1_group.deltime)
        v1_group.part_of_group = group.id
        group_lookup[l2] = group
        ungrouped.remove(l2)
        groups.append(group)
        if top_groups.__contains__(v1_group):
            top_groups.remove(v1_group)
        top_groups.append(group)

    else:
        # Combine the group for v1 and v2
        if l1 == l2:
            return
        group = LocGroup(get_group_num())
        truck = get_truck_req(l1, l2)
        group.add(l1)  # TODO test deltime
        group.add(l2)  # TODO test deltime
        group.truck = truck
        groups.append(group)
        if top_groups.__contains__(l1):
            top_groups.remove(l1)
        if top_groups.__contains__(l2):
            top_groups.remove(l2)
        top_groups.append(group)
        return group


# Helper method for adding vertexes to groups
def get_top_group(group):
    while group.part_of_group is not None:
        top = group.part_of_group
        group = groups[top]
    return group


# A simple method to increment and return the group_num
def get_group_num():
    global group_num
    group_num += 1
    return group_num


# A method to get the truck requirements from 2 items. Args may be a Location or a LocGroup
def get_truck_req(arg_1, arg_2):
    truck_1 = arg_1.truck
    truck_2 = arg_2.truck
    if truck_1 or truck_2:
        if truck_1:
            if truck_2:
                if truck_1 != truck_2:
                    raise Exception("Cannot combine groups with different trucks:", truck_1, "and", truck_2)
                else:
                    return truck_1
            else:
                return truck_1
        else:
            return truck_2
    return None


def check_pkg_availability(time):
    global checkup_time
    global available_locs
    global top_groups
    global groups
    global pkgs
    global group_num
    # Instantiate all variables
    top_groups = []
    groups = []
    group_num = -1

    # If this is the first checkup
    if time == start_time:
        for loc in map.locations:
            # If the location has package that isn't ready
            if loc.ready_at and loc.ready_at > time:
                if checkup_time:
                    checkup_time = loc.ready_at
                else:
                    checkup_time = min(checkup_time, loc.ready_at)
                unavailable_locs.append(loc.id)

            # If the location is ready to go
            else:
                available_locs.append(loc.id)
        # Remove home location
        available_locs.pop(0)

    # If this is a midday checkup
    else:
        for loc in map.locations:
            # For unavailable locations
            if unavailable_locs.__contains__(loc.id):
                # If it's now ready, move to available locations
                if loc.ready_at <= time:
                    available_locs.append(loc.id)
                    unavailable_locs.remove(loc.id)

                # If the location is still not ready, update checkup time
                else:
                    if checkup_time <= time:
                        checkup_time = loc.ready_at
                    else:
                        checkup_time = min(checkup_time, loc.ready_at)

            # For available locations
            else:
                if loc.routed and available_locs.__contains__(loc.id):
                    available_locs.remove(loc.id)
            if len(unavailable_locs) == 0:
                if checkup_time <= time:
                    checkup_time = timedelta(days=99)


# Creates a route from top_groups for a truck with a given id
def create_route(truck):
    route_groups = []
    num_pkgs = 0

    # TODO Remove debug print
    # print("Available groups:")
    # for group in top_groups:
    #     print(group)

    # Add package groups with correct truck requirements
    for group in top_groups:
        if not group.truck or group.truck == truck.id:
            route_groups.append(group)
            num_pkgs += group.pkg_size

    # If we have multiple groups, find the best group to keep
    if len(route_groups) > 1 and num_pkgs > max_packages:
        g1_time = timedelta(days=99)    # Since groups can have a None deltime, use an artificial "long" deltime
        g2_time = timedelta(days=99)
        best = None
        for g1 in route_groups:
            # Set g1_time
            if g1.deltime:
                g1_time = g1.deltime

            # Compare deltimes between each group (only compare the same groups once)
            for g2 in route_groups:
                if g1 == g2:
                    break
                # Set g2_time
                if g2.deltime:
                    g2_time = g2.deltime
                # Have best set to the group with the smallest time
                if g1_time < g2_time:
                    if not best:
                        best = g1
                    elif g1.deltime < best.deltime:
                        best = g1
                elif g1_time > g2_time:
                    if not best:
                        best = g2
                    elif g2.deltime < best.deltime:
                        best = g2
            # Consider trucks
            if g1.truck and g1.deltime:
                if not best or not best.truck:
                    best = g1

        # Re-do route_groups with only best & good groups
        if best:
            route_groups = [best]

    # TODO remove debug statement
    if route_groups:
        print("\nLoaded Truck", truck.id, "with group: ", end='')
        for g in route_groups:
            print(g.id, "", end='')
        print("\n")
    else:
        print("Could not find a group for Truck", truck.id)

    route = route_groups[0]
    if route_groups:
        if len(route_groups) == 1:
            route = route_groups[0]
        else:
            route = create_group(route_groups.pop(), route_groups.pop())
            while len(route_groups) > 0:
                route = create_group(route, route_groups.pop())
        route.make_path(0, map)
        for loc in route.locs:
            for pkg in pkgs.loc_dictionary[loc]:
                truck.packages.append(pkgs.lookup(pkg))
            map.locations[loc].visited = True
            available_locs.remove(loc)
        top_groups.remove(route)

    return route


# Launches the trucks on their route, keeping track of the time as they go
def start_day(status_time):
    clock = timedelta(days=99)
    t_clock = 0     # Which truck has the earliest clock

    # Have all trucks drive, then take the min of truck times
    for truck in trucks:
        pkg = truck.packages[0]
        truck.drive(pkg.loc)
        if truck.time < clock:
            clock = truck.time
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

            # Once there...
            elif len(top_groups) > 0:
                # Try to reload & drive
                if create_route(truck):
                    pkg = truck.packages[0]
                    truck.drive(pkg.loc)
                # If you can't, wait for available packages
                elif unavailable_locs:
                    truck.time = checkup_time
                # If there are no more packages, finished
                else:
                    truck.time = timedelta(days=99)

            # End of day
            else:
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

        # Check for package updates (arrived at hub or # TODO address update)
        if checkup_time <= clock:
            dynamic_group_locs(clock)


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
          "\t3. Display statuses at 12 pm\n"  # TODO delete
          "\t0. Exit")
    try:
        selection = 1  # TODO int(input())
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
    else:
        continue
