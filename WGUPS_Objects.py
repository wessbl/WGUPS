# Author:           Wesley Lancaster
# StudentID:        #001356953
# Date:             September 2020
# WGUPS_Objects.py: Defines all objects and classes necessary for the project

from datetime import timedelta


# A class that represents a Truck object, with
#   id (int)
#   route (list of ints)
#   packages (list of ints that each represent a package in the package hash table)
#   time (datetime)
#   miles (double)
class Truck:
    # Ctor, start time at 8
    def __init__(self, id, speed, max_packages, start_time):
        self.id = id
        self.time = start_time  # start at 8 am
        self.miles = 0.0
        self.speed = speed  # miles per hour
        self.max_packages = max_packages  # max amount of packages
        self.loc = 0  # current location
        self.last_pkg_loc = 0  # the location of its last package
        self.packages = []  # an ordered list of packages (which define the route)

    # Drive the truck (adds time and mileage)
    def drive(self, location):
        dist = Map.distances[self.loc][location]
        self.loc = location
        self.miles += dist
        elapsed = timedelta(hours=dist / self.speed)
        self.time += elapsed

    def add_pkg(self, pkg):
        self.packages.append(pkg)
        self.last_pkg_loc = pkg.loc
        pkg.status = "On truck " + str(self.id)

    def unload(self):
        pkg = self.packages.pop(0)
        pkg.status = "Delivered at " + str(self.time)
        print("Truck", str(self.id), "delivered Pkg", str(pkg.id), "\tto Loc", pkg.loc,
              "\tat", str(self.time), "\twith", round(self.miles, 1), "miles")
        if pkg.deltime and pkg.deltime < self.time:
            error = "Truck " + str(self.id) + " delivered pkg " + str(pkg.id) + " at " + str(self.time) + \
                    ", it was due at " + str(pkg.deltime)
            print(error)
            # TODO raise Exception(error)
        if pkg.truck and pkg.truck != self.id:
            raise Exception("Wrong truck delivered package", pkg.id, ", requires truck", pkg.truck)

    # Truck info in one string
    def __str__(self):
        return "Truck " + str(self.id) + " at " + str(self.time) + ": " + str(round(self.miles, 2)) + " miles"


# A class that represents a Package needing to be delivered, with
#   id (int)
#   loc (int representing a Location obj in the Map class)
#   deadline (time)
#   mass (int)
#   truck (int)
#   arrival_time (time)
#   delivery_time (time)
class Package:
    def __init__(self, id, address, city, zip, deadline, mass, status):
        self.id = id
        self.mass = mass
        self.status = status
        self.truck = None
        self.ready_at = None

        # Assign a location id (for ease) and verify
        self.loc = Map.lookup(address, zip)
        if self.id != -1 & self.loc == -1:
            raise Exception("Unrecognized address!")
        # print("Package", id, "goes to Location", self.loc)

        # Assign a truck requirement for this package
        if status.__contains__("Truck"):
            self.truck = int(status[6])
            Map.locations[self.loc].truck = self.truck
        elif status.__contains__(":"):
            self.ready_at = get_time(status)
            loc = Map.locations[self.loc]
            if loc.ready_at:
                loc.ready_at = max(loc.ready_at, self.ready_at)
            else:
                loc.ready_at = self.ready_at

        # Find out if the package is part of a delivery group

        # Parse deadline, which is in form "10:30 am" or "EOD" (end of day)
        self.deltime = get_time(deadline)
        Map.locations[self.loc].add_deltime(self.deltime)
        # print("Pkg", self.id, "has deadline at", self.deltime)

    def __str__(self):
        return "Pkg#" + str(self.id) + ": " + self.status + ". Loc " + str(self.loc) + " @ " + str(self.deltime)


# Given a string time, return a timedelta. Returns None if string was not valid
def get_time(str_time):
    if type(str_time) == set:
        return None
    str_arr = str_time.split(":")
    if len(str_arr) == 1:
        return None
    hour = int(str_arr[0])
    temp = str_arr[1].split()
    minute = int(temp[0])
    meridiem = temp[1]
    if meridiem == "pm" and hour >= 1:
        hour += 12
    return timedelta(hours=hour, minutes=minute)


# A package-specific node class to be used by the hash_table class, as a node that points to other nodes.
class PkgNode:
    def __init__(self, pkg):
        self.pkg = pkg
        self.next = None


# A hash table with a given array size. Also keeps a dictionary of location->pkgs
class PkgHashTable:
    def __init__(self, arr_size):
        self.arr_size = arr_size
        self.arr = [PkgNode(Package(-1, "", "", "", "", "", ""))]  # -1 is the sign of an empty bucket)
        for i in range(arr_size - 1):
            self.arr.append(PkgNode(Package(-1, "", "", "", "", "", "")))
        self.len = 0
        self.loc_dictionary = {}            # A dictionary that maps a location to packages with that location
        for i in range(len(Map.locations)):
            self.loc_dictionary[i] = []
        self.timelies = []                  # A list for packages with a time constraint
        self.groups = {}                    # A dictionary for packages that need to be grouped (id : {pkg_ids})

    # Insert a new node onto the hash table
    def insert(self, id, address, city, zip, deadline, mass, status="At Warehouse"):
        # TODO Check status for package group
        # if type(status) == set:
        #     self.groups[id] = status
        #     status = "At Warehouse"
        pkg = Package(id, address, city, zip, deadline, mass, status)
        pkg_hash = pkg.id % self.arr_size
        node = self.arr[pkg_hash]  # a node that will help us traverse the hash table
        if node.pkg.id == -1:
            node.pkg = pkg
        else:
            while node.next:
                node = node.next
            node.next = PkgNode(pkg)
        self.len += 1
        self.loc_dictionary[pkg.loc].append(pkg.id)
        if deadline.__contains__(":"):
            self.timelies.append(id)

    # A lookup function that takes a pkg id and returns the Package object with the id; or None if none is found.
    def lookup(self, id):
        pkg_hash = id % self.arr_size
        node = self.arr[pkg_hash]  # a node that will help us traverse the hash table
        if node.pkg.id == -1:  # if it's an empty bucket
            return None
        while node is not None:  # Traverse the linked list until a match is found
            if node.pkg.id == id:
                return node.pkg
            node = node.next
        return None

    # Make class iterable
    def __iter__(self):
        return PkgIterator(self)

    # Defining the string function (for easier debugging)
    def __str__(self):
        s = ""
        for i in range(self.arr_size):
            s += str(i) + ":\t\t"
            node = self.arr[i]
            while node is not None:
                s += str(node.pkg.id) + "\t"
                node = node.next
            s += "\n"
        return s


# An iterator class for the hash table
class PkgIterator:
    def __init__(self, pkgs):
        self.pkgs = pkgs
        self.index = 0

    # Figure out which package to return next
    def __next__(self):
        self.index += 1
        if self.index > self.pkgs.len:
            self.index = 0
            raise StopIteration
        return self.pkgs.lookup(self.index)


# A method that inserts package data into our hash table.
def load_pkgs(pkgs):
    pkgs.insert(1, "195 W Oakland Ave", "Salt Lake City", "84115", "10:30 AM", 21)                          # Loc 5
    pkgs.insert(2, "2530 S 500 E", "Salt Lake City", "84106", "EOD", 44)                                    # Loc 9
    pkgs.insert(3, "233 Canyon Rd", "Salt Lake City", "84103", "EOD", 2, "Truck 2 Required")                # Loc 8
    pkgs.insert(4, "380 W 2880 S", "Salt Lake City", "84115", "EOD", 4)                                     # Loc 18
    pkgs.insert(5, "410 S State St", "Salt Lake City", "84111", "EOD", 5)                                   # Loc 19
    pkgs.insert(6, "3060 Lester St", "West Valley City", "84119", "10:30 AM", 88, "9:05 am")                # Loc 13
    pkgs.insert(7, "1330 2100 S", "Salt Lake City", "84106", "EOD", 8)                                      # Loc 2
    pkgs.insert(8, "300 State St", "Salt Lake City", "84103", "EOD", 9)                                     # Loc 12
    pkgs.insert(9, "300 State St", "Salt Lake City", "84103", "EOD", 2)  # "Wrong address listed            # Loc 12
    pkgs.insert(10, "600 E 900 South", "Salt Lake City", "84105", "EOD", 1)                                 # Loc 25
    pkgs.insert(11, "2600 Taylorsville Blvd", "Salt Lake City", "84118", "EOD", 1)                          # Loc 10
    pkgs.insert(12, "3575 W Valley Central Station bus Loop", "West Valley City", "84119", "EOD", 1)        # Loc 16
    pkgs.insert(13, "2010 W 500 S", "Salt Lake City", "84104", "10:30 AM", 2)                               # Loc 6
    pkgs.insert(14, "4300 S 1300 E", "Millcreek", "84117", "10:30 AM", 88, {15, 19})                        # Loc 20
    pkgs.insert(15, "4580 S 2300 E", "Holladay", "84117", "9:00 AM", 4)                                     # Loc 21
    pkgs.insert(16, "4580 S 2300 E", "Holladay", "84117", "10:30 AM", 88, {13, 19})                         # Loc 21
    pkgs.insert(17, "3148 S 1100 W", "Salt Lake City", "84119", "EOD", 2)                                   # Loc 14
    pkgs.insert(18, "1488 4800 S", "Salt Lake City", "84123", "EOD", 6, "Truck 2 Required")                 # Loc 3
    pkgs.insert(19, "177 W Price Ave", "Salt Lake City", "84115", "EOD", 37)                                # Loc 4
    pkgs.insert(20, "3595 Main St", "Salt Lake City", "84115", "10:30 AM", 37, {13, 15})                    # Loc 17
    pkgs.insert(21, "3595 Main St", "Salt Lake City", "84115", "EOD", 3)                                    # Loc 17
    pkgs.insert(22, "6351 South 900 East", "Murray", "84121", "EOD", 2)                                     # Loc 26
    pkgs.insert(23, "5100 South 2700 West", "Salt Lake City", "84118", "EOD", 5)                            # Loc 23
    pkgs.insert(24, "5025 State St", "Murray", "84107", "EOD", 7)                                           # Loc 22
    pkgs.insert(25, "5383 South 900 East #104", "Salt Lake City", "84117", "10:30 AM", 7, "9:05 am")        # Loc 24
    pkgs.insert(26, "5383 South 900 East #104", "Salt Lake City", "84117", "EOD", 25)                       # Loc 24
    pkgs.insert(27, "1060 Dalton Ave S", "Salt Lake City", "84104", "EOD", 5)                               # Loc 1
    pkgs.insert(28, "2835 Main St", "Salt Lake City", "84115", "EOD", 7, "9:05 am")                         # Loc 11
    pkgs.insert(29, "1330 2100 S", "Salt Lake City", "84106", "10:30 AM", 2)                                # Loc 2
    pkgs.insert(30, "300 State St", "Salt Lake City", "84103", "10:30 AM", 1)                               # Loc 12
    pkgs.insert(31, "3365 S 900 W", "Salt Lake City", "84119", "10:30 AM", 1)                               # Loc 15
    pkgs.insert(32, "3365 S 900 W", "Salt Lake City", "84119", "EOD", 1, "9:05 am")                         # Loc 15
    pkgs.insert(33, "2530 S 500 E", "Salt Lake City", "84106", "EOD", 1)                                    # Loc 9
    pkgs.insert(34, "4580 S 2300 E", "Holladay", "84117", "10:30 AM", 2)                                    # Loc 21
    pkgs.insert(35, "1060 Dalton Ave S", "Salt Lake City", "84104", "EOD", 88)                              # Loc 1
    pkgs.insert(36, "2300 Parkway Blvd", "West Valley City", "84119", "EOD", 88, "Truck 2 Required")        # Loc 7
    pkgs.insert(37, "410 S State St", "Salt Lake City", "84111", "10:30 AM", 2)                             # Loc 19
    pkgs.insert(38, "410 S State St", "Salt Lake City", "84111", "EOD", 9, "Truck 2 Required")              # Loc 19
    pkgs.insert(39, "2010 W 500 S", "Salt Lake City", "84104", "EOD", 9)                                    # Loc 6
    pkgs.insert(40, "380 W 2880 S", "Salt Lake City", "84115", "10:30 AM", 45)                              # Loc 18


# A class that represents a location to deliver a package to, with
#   id (int)
#   name (string)
#   address (string)
class Location:
    """A location object with ID, name, and address at minimum"""

    def __init__(self, id, name, address, zip):
        self.id = id
        self.name = name
        self.address = address
        self.zip = zip
        self.deltime = None
        self.truck = None
        self.all_pkgs_available = True  # Assume all pkgs are available
        self.ready_at = None
        self.routed = False     # Location been added to a route

    def to_string(self):
        return self.id + "\t" + self.name + "\t" + self.address

    def add_deltime(self, deltime):
        if self.deltime:
            if deltime and deltime < self.deltime:
                self.deltime = deltime
        else:
            self.deltime = deltime


# A location group class, which will help us keep track of the order in which location groups are visited.
class LocGroup:
    def __init__(self, id):
        self.id = id
        self.pair = []      # The two location entities that are paired by this group, may be an int or a LocGroup obj
        self.locs = []      # The list of all locations that this group and other groups own
        self.size = 0
        self.pkg_size = 0           # How many packages are represented by this group
        self.part_of_group = None
        self.center = None
        self.deltime = None         # earliest delivery time
        self.mileage_cost = None    # How many miles are spent in the group
        self.dividable = True
        self.truck = None

    # Add a location or group of locations to the group
    def add(self, loc, pkgs_added=0, truck_requirement=None, deltime=None):
        self.pair.append(loc)
        self.truck = truck_requirement

        # Update size, pkg_size & locs
        if type(loc) == LocGroup:
            self.size += loc.size
            self.pkg_size += loc.pkg_size
            for l in loc:
                self.locs.append(l)
        else:
            self.size += 1
            self.pkg_size += pkgs_added
            self.locs.append(loc)

        # TODO Define a group-wide delivery time
        if type(loc) == LocGroup:
            if self.deltime is None or loc.deltime and loc.deltime < self.deltime:
                self.deltime = loc.deltime
        elif deltime is not None:
            if self.deltime is None or deltime < self.deltime:
                self.deltime = deltime

        # If this is the first added location/group, set center to be equal to the location/group's center
        if self.center is None:
            if type(loc) == LocGroup:
                self.center = loc.center
            else:
                self.center = loc

        # If this is the second loc/group, define a new center
        else:
            # Redefine the center vertex (the one with the lowest sum of edges going to other vertexes in the group)
            verts = {}  # Dictionary (loc index -> sum of edges)
            for i in self.locs:
                for j in self.locs:
                    if i in verts.keys():
                        verts[i] += Map.distances[i][j]  # Sum the edges
                    else:
                        verts[i] = Map.distances[i][j]

            # Get the key holding the minimal value
            keys = list(verts.keys())
            values = list(verts.values())
            min = sorted(values)[0]
            self.center = keys[values.index(min)]   # Get index of minimum value, then use it to look up the key

    # Once vertices are finalized for the group, call this method to make the path within this group. Updates locs
    def make_path(self, from_vertex, map):
        # TODO add consideration for timelies first; if necessary, ungroup and have other truck deliver part of the grp
        # For each member of the pair, get the integer id of the location, or the center if it's a group, and deltimes
        first = self.pair[0]
        second = self.pair[1]
        first_is_group = False
        second_is_group = False
        self.locs = []

        # Check for groups in the pair
        if type(first) == LocGroup:
            first_is_group = True
            first_dt = first.deltime
            first = first.center
        else:
            first_dt = Map.locations[first].deltime
        if type(second) == LocGroup:
            second_is_group = True
            second_dt = second.deltime
            second = second.center
        else:
            second_dt = Map.locations[second].deltime

        # Check if we need to swap the order of the pair, for timeliness or closeness. The pair is treated like [a, b]
        # Compare the distance from the given vertex to each member of the pair, set a_closer = (a is closer than b?)
        swapped = False
        distances = map.min_dist(from_vertex, [first, second])
        if distances[0][0] == second:
            a_closer = False
        else:
            a_closer = True

        # Swap if a is neither timely nor close
        if not first_dt and not a_closer:
            self.swap_pair()
            swapped = True

        # Check if we have only one timely vertex that is further away
        elif not first_dt and second_dt and a_closer:
            self.swap_pair()    # TODO if we can visit a first? done : swap
            swapped = True
        # elif a_dt and not b_dt and not a_closer:
            # TODO if we can visit b first? swap : done

        # Check if both are timely
        if first_dt and second_dt:
            if not a_closer and first_dt >= second_dt:
                self.swap_pair()
                swapped = True
            # elif not a_closer:
                # TODO visit b first? swap
            elif second_dt < first_dt:
                # TODO visit a first? done: swap
                self.swap_pair()
                swapped = True

        if swapped:
            temp = first
            first = second
            second = temp
            temp = first_is_group
            first_is_group = second_is_group
            second_is_group = temp

        # Recursively visit groups in the pair to swap and rebuild locs
        # Add first loc(s)
        if first_is_group:
            self.locs = self.pair[0].make_path(from_vertex, map)
        else:
            self.locs.append(first)
        # Add second loc(s)
        if second_is_group:
            # For each loc found in second group, emphasizing closeness to the last vertex added by first loc(s)
            for loc in self.pair[1].make_path(self.locs[len(self.locs) - 1], map):
                self.locs.append(loc)
        else:
            self.locs.append(second)

        return self.locs

    # Swaps the order of the pair in the group
    def swap_pair(self):
        temp = self.pair[0]
        self.pair[0] = self.pair[1]
        self.pair[1] = temp

    # If the time spent within this group wholly exceeds a delivery time, or
    def subdivide(self):
        if self.dividable:
            print("hello! this method has not been implemented yet. Have a nice day!")
        else:
            raise Exception("Group cannot be subdivided!")

    def __iter__(self):
        return LocIter(self.locs)

    # Returns a high-level overview of the group
    def overview(self):
        string = "Grp " + str(self.id) + ":"
        string += "\tPkgs=" + str(self.pkg_size)
        if self.deltime:
            string += "\tDelTime=" + str(self.deltime.seconds//3600) + ":"
            minutes = (self.deltime.seconds//60) % 60
            if minutes < 10:
                string += "0" + str(minutes)
            else:
                string += str(minutes)
        if self.truck:
            string += "\tTrk=" + str(self.truck)
        return string

    # To String
    def __str__(self):
        string = "(Grp " + str(self.id) + ": "
        string += str(self.pair[0]) + ", " + str(self.pair[1])
        string += ", Ctr=" + str(self.center)
        if self.truck:
            string += ", T=" + str(self.truck)
        if self.deltime:
            string += ", DT=" + str(self.deltime.seconds//3600) + ":"
            minutes = (self.deltime.seconds//60) % 60
            if minutes < 10:
                string += "0" + str(minutes)
            else:
                string += str(minutes)
        string += ", Pkgs=" + str(self.pkg_size)
        return string + ")"


# Iteration class for location groups
class LocIter:
    def __init__(self, locs):
        self.all_locs = self.explore_locs(locs)
        self.index = -1

    def __next__(self):
        self.index += 1
        if self.index == len(self.all_locs):
            raise StopIteration
        return self.all_locs[self.index]

    def explore_locs(self, locs):
        all_locs = []
        for l in locs:
            if type(l) == LocGroup:
                for l in self.explore_locs(l.locs):
                    all_locs.append(l)
            else:
                all_locs.append(l)
        return all_locs


# A class containing a hash table of all locations, as well as an adjacency matrix
class Map:
    locations = [
        Location(0, "Western Governors University", "4001 South 700 East", "84107"),
        Location(1, "International Peace Gardens", "1060 Dalton Ave S", "84104"),
        Location(2, "Sugar House Park", "1330 2100 S", "84106"),
        Location(3, "Taylorsville-Bennion Heritage City Gov Off", "1488 4800 S", "84123"),
        Location(4, "Salt Lake City Division of Health Services", "177 W Price Ave", "84115"),
        Location(5, "South Salt Lake Public Works", "195 W Oakland Ave", "84115"),
        Location(6, "Salt Lake City Streets and Sanitation", "2010 W 500 S", "84104"),
        Location(7, "Deker Lake", "2300 Parkway Blvd", "84119"),
        Location(8, "Salt Lake City Ottinger Hall", "233 Canyon Rd", "84103"),
        Location(9, "Columbus Library", "2530 S 500 E", "84106"),
        Location(10, "Taylorsville City Hall", "2600 Taylorsville Blvd", "84118"),
        Location(11, "South Salt Lake Police", "2835 Main St", "84115"),
        Location(12, "Council Hall", "300 State St", "84103"),
        Location(13, "Redwood Park", "3060 Lester St", "84119"),
        Location(14, "Salt Lake County Mental Health", "3148 S 1100 W", "84119"),
        Location(15, "Salt Lake County/United Police Dept", "3365 S 900 W", "84119"),
        Location(16, "West Valley Prosecutor", "3575 W Valley Central Station bus Loop", "84119"),
        Location(17, "Housing Auth. of Salt Lake County", "3595 Main St", "84115"),
        Location(18, "Utah DMV Administrative Office", "380 W 2880 S", "84115"),
        Location(19, "Third District Juvenile Court", "410 S State St", "84111"),
        Location(20, "Cottonwood Regional Softball Complex", "4300 S 1300 E", "84117"),
        Location(21, "Holiday City Office", "4580 S 2300 E", "84117"),
        Location(22, "Murray City Museum", "5025 State St", "84107"),
        Location(23, "Valley Regional Softball Complex", "5100 South 2700 West", "84118"),
        Location(24, "City Center of Rock Springs", "5383 South 900 East #104", "84117"),
        Location(25, "Rice Terrace Pavilion Park", "600 E 900 South", "84105"),
        Location(26, "Wheeler Historic Farm", "6351 South 900 East", "84121")
    ]
    distances = [
        [0],                                                                                                        # 0
        [7.2, 0],
        [3.8, 7.1, 0],
        [11.0, 6.4, 9.2, 0],
        [2.2, 6.0, 4.4, 5.6, 0],
        [3.5, 4.8, 2.8, 6.9, 1.9, 0],
        [10.9, 1.6, 8.6, 8.6, 7.9, 6.3, 0],
        [8.6, 2.8, 6.3, 4.0, 5.1, 4.3, 4.0, 0],
        [7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0],
        [2.8, 6.3, 1.6, 7.3, 2.6, 1.5, 8.0, 9.3, 4.8, 0],
        [6.4, 7.3, 10.4, 1.0, 6.5, 8.7, 8.6, 4.6, 11.9, 9.4, 0],                                                    # 10
        [3.2, 5.3, 3.0, 6.4, 1.5, 0.8, 6.9, 4.8, 4.7, 1.1, 7.3, 0],
        [7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0.6, 5.1, 12.0, 4.7, 0],
        [5.2, 3.0, 6.5, 3.9, 3.2, 3.9, 4.2, 1.6, 7.6, 4.6, 4.9, 3.5, 7.3, 0],
        [4.4, 4.6, 5.6, 4.3, 2.4, 3.0, 8.0, 3.3, 7.8, 3.7, 5.2, 2.6, 7.8, 1.3, 0],
        [3.7, 4.5, 5.8, 4.4, 2.7, 3.8, 5.8, 3.4, 6.6, 4.0, 5.4, 2.9, 6.6, 1.5, 0.6, 0],                             # 15
        [7.6, 7.4, 5.7, 7.2, 1.4, 5.7, 7.2, 3.1, 7.2, 6.7, 8.1, 6.3, 7.2, 4.0, 6.4, 5.6, 0],
        [2.0, 6.0, 4.1, 5.3, 0.5, 1.9, 7.7, 5.1, 5.9, 2.3, 6.2, 1.2, 5.9, 3.2, 2.4, 1.6, 7.1, 0],
        [3.6, 5.0, 3.6, 6.0, 1.7, 1.1, 6.6, 4.6, 5.4, 1.8, 6.9, 1.0, 5.4, 3.0, 2.2, 1.7, 6.1, 1.6, 0],
        [6.5, 4.8, 4.3, 10.6, 6.5, 3.5, 3.2, 6.7, 1.0, 4.1, 11.5, 3.7, 1.0, 6.9, 6.8, 6.4, 7.2, 4.9, 4.4, 0],
        [1.9, 9.5, 3.3, 5.9, 3.2, 4.9, 11.2, 8.1, 8.5, 3.8, 6.9, 4.1, 8.5, 6.2, 5.3, 4.9, 10.6, 3.0, 4.6, 7.5, 0],  # 20
        [3.4, 10.9, 5.0, 7.4, 5.2, 6.9, 12.7, 10.4, 10.3, 5.8, 8.3, 6.2, 10.3, 8.2, 7.4, 6.9, 12.0, 5.0, 6.6, 9.3,
         2.0, 0],
        [2.4, 8.3, 6.1, 4.7, 2.5, 4.2, 10.0, 7.8, 7.8, 4.3, 4.1, 3.4, 7.8, 5.5, 4.6, 4.2, 9.4, 2.3, 3.9, 6.8, 2.9,
         4.4, 0],
        [6.4, 6.9, 9.7, 0.6, 6.0, 9.0, 8.2, 4.2, 11.5, 7.8, 0.4, 6.9, 11.5, 4.4, 4.8, 5.6, 7.5, 5.5, 6.5, 11.4, 6.4,
         7.9, 4.5, 0],
        [2.4, 10.0, 6.1, 6.4, 4.2, 5.9, 11.7, 9.5, 9.5, 4.8, 4.9, 5.2, 9.5, 7.2, 6.3, 5.9, 11.1, 4.0, 5.6, 8.5, 2.8,
         3.4, 1.7, 5.4, 0],
        [5.0, 4.4, 2.8, 10.1, 5.4, 3.5, 5.1, 6.2, 2.8, 3.2, 11.0, 3.7, 2.8, 6.4, 6.5, 5.7, 6.2, 5.1, 4.3, 1.8, 6.0,
         7.9, 6.8, 10.6, 7.0, 0],
        [3.6, 13.0, 7.4, 10.1, 5.5, 7.2, 14.2, 10.7, 14.1, 6.0, 6.8, 6.4, 14.1, 10.5, 8.8, 8.4, 13.6, 5.2, 6.9,
         13.1, 4.1, 4.7, 3.1, 7.8, 1.3, 8.3, 0]                                                                     # 26
    ]

    # Fill out the adjacency matrix for easier use later, also get the avg length and create groups for shortest lengths
    # for every vertex
    def __init__(self):
        self.avg_len = 0.0
        size = len(self.distances)
        for i in range(size):
            for j in range(size):
                try:
                    self.avg_len += self.distances[i][j]
                except:
                    self.distances[i].append(self.distances[j][i])
        total_edges = size * (size - 1) / 2
        self.avg_len /= total_edges

    # Return a list of tuples (index, dist) for indexes adjacent to the given location.
    # Option to give a list of indexes for desired adjacent locations. Ignores distance to self
    def min_dist(self, x, adj_list=[]):
        adj_dict = {}
        # If a list was provided
        if len(adj_list) > 0:
            for i in adj_list:
                if i != x:
                    adj_dict[i] = self.distances[x][i]
        # Return all adjacencies
        else:
            for i in range(len(self.distances)):
                if i != x:
                    adj_dict[i] = self.distances[x][i]
        return sorted(adj_dict.items(), key=lambda x: x[1])

    # Looks up address and zip for a match, then returns a location id if a match is found
    @staticmethod
    def lookup(address, zip):
        for l in Map.locations:
            if l.zip == zip and l.address == address:
                return l.id
        return -1