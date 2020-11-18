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
full_cluster = []


# * * * * *   Simulate Function   * * * * * #
# Simulates the WGUPS workday, printing package status updates between 2 given times. This function
# is the "clock" of the simulation, its only logic is to make sure the timeline is correct. Other functions are used for
# the actual algorithm
def simulate(status_time):
    global pkgs
    global trucks
    global full_cluster
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
    for pkg in pkgs:
        if manage_clusters(pkg):
            cluster = manage_clusters(pkg)
    if cluster:
        for pkg in cluster:
            pkg = pkgs.lookup(pkg)
            pkg.cluster = cluster
            map.locations[pkg.loc].clustered = True
        full_cluster = cluster

    # 1- Group locations and load trucks with their packages
    dynamic_group_locs(start_time)
    for truck in trucks:
        create_route(truck)

    # 2- Initiate simulation, keeping track of the time
    start_day(status_time)

    # Status Report
    # print("Status Report for ", pkgs.len, " packages:")
    for pkg in pkgs:
        if not pkg.status.__contains__("Delivered"):
            error = "Package #" + str(pkg.id) + " was undelivered at end of day."
            print(error)
            # raise Exception(error)    # TODO
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


# The dynamic algorithm that assigns packages based on location
def dynamic_group_locs(time, locs=None):
    # Create variables needed for this method
    global full_cluster
    group_lookup = {}  # A dictionary of all group objects, with all ids pointing to their group
    if locs:
        ungrouped = locs  # A list of Location ids that haven't been grouped yet
    else:
        check_pkg_availability(time)
        ungrouped = available_locs.copy()  # A list of Location ids that haven't been grouped yet

    # Check if only one location is available
    if len(ungrouped) == 1:
        group = LocGroup(get_group_num())
        loc = map.locations[ungrouped[0]]
        group.add(loc.id, len(pkgs.loc_dictionary[loc.id]), loc.truck, loc.deltime)
        group_lookup[loc.id] = group
        ungrouped.remove(loc.id)
        groups.append(group)
        top_groups.append(group)
        return

    # Make the cluster into a special group
    if full_cluster:
        cluster_locs = []
        # There can't be a package that is both unavailable and clustered, so group immediately
        # are delivered to it
        for pkg in full_cluster:
            pkg = pkgs.lookup(pkg)
            # Get all the locations for the pkgs in the cluster
            if not cluster_locs.__contains__(pkg.loc):
                cluster_locs.append(pkg.loc)
            # Remove this loc from ungrouped for this frame (it'll be grouped in its own frame)
            if ungrouped.__contains__(pkg.loc):
                ungrouped.remove(pkg.loc)
        full_cluster = None
        dynamic_group_locs(time, cluster_locs)  # Group only the cluster locs

    # Make sure all locations are in a group, starting with shortest edges
    group_shortest_edges(ungrouped, False, group_lookup)

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
        closest_ctr = []  # Holds closest center       closest_ctr[row][pair](vertex, distance)
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
        a = small_groups[index_1]
        b = small_groups[index_2]

        # Get a new pair if the groups are not combinable (pkg_size limit or truck requirements)
        while a.pkg_size + b.pkg_size > max_packages or a.truck != b.truck:
            # There's a bad pairing, remove it from closest_centers and re-do distances
            closest_ctr[index_1].pop(0)
            if closest_ctr[index_1]:
                distances[index_1] = closest_ctr[index_1][0][1]
            # If there's no more pairings left for this group, remove it from everything
            else:
                small_groups.remove(a)
                centers.pop(index_1)
                closest_ctr.pop(index_1)
                distances.pop(index_1)
                index_2 -= 1    # Decrement because index_1, which is less than index_2, has been removed

            closest_ctr[index_2].pop(0)
            if closest_ctr[index_2]:
                distances[index_2] = closest_ctr[index_2][0][1]
            # If there's no more pairings left for this group, remove it from everything
            else:
                small_groups.remove(b)
                centers.pop(index_2)
                closest_ctr.pop(index_2)
                distances.pop(index_2)

            # Find indexes for lowest distance, and the pair to the vertex with the lowest distance
            min_d = min(distances)
            index_1 = distances.index(min_d)
            index_2 = centers.index(closest_ctr[index_1][0][0])
            # Get closest top groups a,b
            a = small_groups[index_1]
            b = small_groups[index_2]

        small_groups.remove(a)
        small_groups.remove(b)
        group = combine_groups(a, b)

        # Add new group to small_groups if it's still small enough to be combined
        if group.pkg_size + smallest_size <= max_packages:
            small_groups.append(group)

        # Update smallest_size
        if a.pkg_size == smallest_size or b.pkg_size == smallest_size:
            smallest_size = group.pkg_size
            for g in small_groups:
                smallest_size = min(smallest_size, g.pkg_size)
        # print("Combined groups", a.id, ",", b.id, "at distance of", min(distances))  # Debug print
    return


# Takes a list of locations and groups by shortest edges
def group_shortest_edges(ungrouped, fully_group, group_lookup={}):
    these_groups = []
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

            if fully_group:
                # Add vertices to a group if one is still ungrouped
                if ungrouped.__contains__(v1) or ungrouped.__contains__(v2):
                    these_groups = create_group(v1, v2, ungrouped, group_lookup)
                # Combine groups if no location is ungrouped
                if not ungrouped:
                    g1 = get_top_group(group_lookup[v1])
                    g2 = get_top_group(group_lookup[v2])
                    if g1 is not g2:
                        these_groups = combine_groups(g1, g2)  # If fully_group, we only need the top group
            else:
                # Add vertices to a group if one is still ungrouped
                if ungrouped.__contains__(v1) or ungrouped.__contains__(v2):
                    group = create_group(v1, v2, ungrouped, group_lookup)
                    these_groups.append(group)

            # Added. Now check if we need to escape loops
            if not fully_group and len(ungrouped) == 0:
                break
        if not fully_group and len(ungrouped) == 0:
            break

    return these_groups


# A method that adds two locations to a single group, or groups one vertex with another group. l1 and l2 must be
# location IDs. Combines groups, do not use on a loop!
def create_group(l1, l2, ungrouped=[], group_lookup=None):

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
            return group

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
            return group

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
        top_groups.remove(v1_group)
        top_groups.append(group)
        return group

    else:
        # Combine the group for v1 and v2
        v1_group = group_lookup[l1]
        v1_group = get_top_group(v1_group)  # Only deal with top groups
        v2_group = group_lookup[l2]
        v2_group = get_top_group(v2_group)  # Only deal with top groups
        return combine_groups(v1_group, v2_group)


# A method that combines two different groups into a single group. Differs from create_group because it requires groups
def combine_groups(g1, g2):
    if g1 == g2:
        return g1
    g1 = get_top_group(g1)
    g2 = get_top_group(g2)
    truck = get_truck_req(g1, g2)
    group = LocGroup(get_group_num())
    group.add(g1)
    group.add(g2)
    g1.part_of_group = group.id
    g2.part_of_group = group.id
    group.truck = truck
    groups.append(group)
    if top_groups.__contains__(g1):
        top_groups.remove(g1)
    if top_groups.__contains__(g2):
        top_groups.remove(g2)
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

            # For available locations, remove fully delivered locs and update others
            elif loc.routed and available_locs.__contains__(loc.id):
                available_locs.remove(loc.id)
            else:
                truck = None
                deltime = None
                for pkg in pkgs.loc_dictionary[loc.id]:
                    pkg = pkgs.lookup(pkg)
                    if pkg.truck and not truck:
                        truck = pkg.truck
                    if pkg.deltime:
                        if deltime:
                            deltime = min(deltime, pkg.deltime)
                        else:
                            deltime = pkg.deltime
                loc.deltime = deltime
                loc.truck = truck

            if len(unavailable_locs) == 0:
                if checkup_time <= time:
                    checkup_time = timedelta(days=99)
    return


# Creates a route from top_groups for a truck with a given id
def create_route(truck):
    route_groups = []
    num_pkgs = 0

    # TODO Remove debug print
    print("\nTruck", truck.id, "arrived at hub. Available groups:")
    for group in top_groups:
        print(group.overview())

    # Add package groups with correct truck requirements
    for group in top_groups:
        if not group.truck or group.truck == truck.id:
            route_groups.append(group)
            num_pkgs += group.pkg_size

    # If we have multiple groups, find the best group to keep (the soonest delivery time that has a truck req)
    route = None
    if len(route_groups) > 1:
        if num_pkgs > max_packages:
            g1_time = timedelta(days=99)    # Since groups can have a None deltime, use an artificial "long" deltime
            g2_time = timedelta(days=99)
            best = None

            # Find soonest delivery time
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
                    else:
                        continue
                    # Have best set to the group with the smallest time
                    if g1_time < g2_time:
                        if not best or not best.deltime or g1.deltime < best.deltime:
                            best = g1
                    elif g1_time > g2_time:
                        if not best or not best.deltime or g2.deltime < best.deltime:
                            best = g2

                # Always give truck requirements priority
                if g1.truck:
                    if not best or not best.truck:
                        best = g1

            # Create the route
            if best:
                route = best
            else:
                route = route_groups[0]     # No timelies/truck reqs, so just assign it the first group

        # If the truck can fit all packages
        else:
            locs = []
            for group in route_groups:
                for loc in group.locs:
                    locs.append(loc)
            route = group_shortest_edges(locs, True)

    # If only one route was selected in route_groups
    else:
        route = route_groups[0]

    # For the last delivery, visit the timely locations first (at the expense of miles)
    if checkup_time == timedelta(days=99) and len(route.locs) > 8 and route.pair[0].deltime and route.pair[1].deltime:
        top_groups.remove(route)
        timelies = []
        regulars = []
        for loc in route.locs:
            if map.locations[loc].deltime:
                timelies.append(loc)
            else:
                regulars.append(loc)

        # Group all the timelies together, then the regulars in a separate group, then group them together
        timelies = group_shortest_edges(timelies, True)
        regulars = group_shortest_edges(regulars, True)
        if regulars:
            route = combine_groups(timelies, regulars)

    # Make a good path to traverse the route
    route.make_path(0, map)

    # Add all packages from all locations in the route
    for loc in route.locs:
        # If it's clustered, don't add unavailable packages, and keep the loc available if there are any
        if map.locations[loc].clustered:
            all_pkgs_loaded = True
            for pkg in pkgs.loc_dictionary[loc]:
                pkg = pkgs.lookup(pkg)
                # Load all available packages, flag if there's one that's unavailable
                if not pkg.ready_at or pkg.ready_at <= truck.time:
                    truck.load(pkg)
                else:
                    all_pkgs_loaded = False
            if all_pkgs_loaded:
                map.locations[loc].routed = True
                available_locs.remove(loc)

        # If it's not clustered, add all undelivered packages and make location unavailable
        else:
            for pkg in pkgs.loc_dictionary[loc]:
                pkg = pkgs.lookup(pkg)
                if pkg.ready_at and pkg.ready_at > truck.time:
                    raise Exception("Loaded package that was unavailable!")
                # Check status and update if needed
                if pkg.status != "At Warehouse":
                    stat = pkg.status
                    if type(stat) == str:
                        if stat.__contains__("Truck") or stat.__contains__(":"):
                            truck.load(pkg)
                        else:
                            raise Exception("Package #", pkg.id, "has a bad status: ", pkg.status)
                    elif type(stat) == list:
                        truck.load(pkg)
                    else:
                        raise Exception("Package #", pkg.id, "has a bad status: ", pkg.status)
                else:
                    truck.load(pkg)
            map.locations[loc].routed = True
            available_locs.remove(loc)

    print("Loaded truck", truck.id, "with", route.overview(), "\n")
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
        pkg = None
        if truck.packages:
            pkg = truck.packages[0]
        while truck.packages and truck.loc == pkg.loc:
            # Check for package #9, which has the wrong address
            if pkg.id == 9 and pkg.loc == 12:
                pkg = truck.packages.pop(0)
                pkgs.loc_dictionary[pkg.loc].remove(pkg.id)
                pkg.loc = None  # Ensures that pkg will not be delivered until address is updated
                pkg.ready_at = timedelta(days=99)
                truck.load(pkg)  # Put package at end of list, truck will drop it off at hub
            else:
                truck.unload()
                pkgs.loc_dictionary[pkg.loc].remove(pkg.id)
            if truck.packages:
                pkg = truck.packages[0]

        # If truck is empty, or if it needs to return a package
        if len(truck.packages) == 0 or truck.packages[0].loc is None:

            # Go back to warehouse
            if truck.loc != 0:
                truck.drive(0)

            # If at the warehouse
            else:
                # See if the truck has brought a package back
                if truck.packages:
                    for pkg in truck.packages:
                        print("\nDropped off Package #", pkg.id, "at hub due to bad address")
                        pkg.status = "At Warehouse"
                    truck.packages = []

                # Check if more deliveries need to be made
                if len(top_groups):
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

        # Drive to next package's location
        else:
            pkg = truck.packages[0]
            if pkg.loc:
                truck.drive(pkg.loc)
            else:
                truck.drive(0)

        # Configure clock
        clock = timedelta(days=99)
        for truck in trucks:
            if truck.time < clock:
                clock = truck.time
                t_clock = truck.id

        # Update Pkg #9's address at 10:20 am
        if timedelta(hours=10, minutes=20) <= clock and (not pkgs.lookup(9).loc or pkgs.lookup(9).loc == 12):
            loc = map.lookup("410 S State St", "84111")
            if loc == -1:
                raise Exception("Bad address given!")
            pkg = pkgs.lookup(9)
            pkg.loc = loc
            pkgs.loc_dictionary[loc].append(pkg.id)
            pkg.ready_at = None
            loc = map.locations[loc]
            loc.routed = False
            if not available_locs.__contains__(loc.id):
                available_locs.append(loc.id)
            if pkg.status.__contains__("On Truck"):
                t = int(pkg.status[9:9])
                # Check if the truck with Pkg 9 is currently in transit (not held by 'truck')
                if trucks[t - 1] != truck:
                    truck = trucks[truck - 1]
                dynamic_group_pkgs(truck)
            print("\nUpdated address for Pkg 9, ready for delivery\n")
            dynamic_group_locs(clock)

        # Check for package updates (arrived at hub or # TODO address update)
        if checkup_time <= clock:
            dynamic_group_locs(checkup_time)


# A method for re-routing a truck while it's already making deliveries
def dynamic_group_pkgs(truck):
    locs = []
    for pkg in truck.packages:
        if not locs.__contains__(pkg.loc):
            locs.append(pkg.loc)


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