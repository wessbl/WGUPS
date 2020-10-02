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
    def __init__(self, id, speed, max_packages):
        self.id = id
        self.time = timedelta(hours=8)  # start at 8 am
        self.miles = 0.0
        self.speed = speed  # miles per hour
        self.max_packages = max_packages  # max amount of packages
        self.location = 0  # current location
        self.last_pkg_loc = 0  # the location of its last package
        self.packages = []  # an ordered list of packages (which define the route)

    # Drive the truck (adds time and mileage)
    def drive(self, dist):
        self.miles += dist
        elapsed = timedelta(hours=dist / self.speed)
        self.time += elapsed
        print("Truck ", self.id, " drove ", dist, " miles", sep='')

    def add_pkg(self, pkg):
        self.packages.append(pkg)
        self.last_pkg_loc = pkg.loc_id

    # Truck info in one string
    def __str__(self):
        return "Truck " + str(self.id) + " at " + str(self.time) + ": " + str(self.miles) + " miles"


# A class that represents a Package needing to be delivered, with
#   id (int)
#   destination (int representing a location in the loc_table)
#   deadline (time)
#   mass (int)
#   truck (int)
#   pkg_group (list of ints)
#   arrival_time (time)
#   delivery time (time)
class Package:
    def __init__(self, id, address, city, zip, deadline, mass, status):
        self.id = id
        self.address = address
        self.city = city
        self.zip = zip
        self.mass = mass
        self.status = status
        self.truck = None
        self.pkg_group = None

        # Assign a location id (for ease) and, if it's a real address, verify a valid loc_id
        self.loc_id = Map.lookup(address, zip)
        if self.id != -1 & self.loc_id == -1:
            raise Exception("Unrecognized address!")

        # Parse deadline, which is in form "10:30 am" or "EOD" (end of day)
        dl = deadline.split(":")
        if len(dl) > 1:  # if we have a time deadline
            hour = int(dl[0])
            temp = dl[1].split()
            minute = int(temp[0])
            meridiem = temp[1]
            if meridiem == "pm" and hour >= 1:
                hour += 12
            self.deadline = timedelta(hours=hour, minutes=minute)

    def __str__(self):
        return "Pkg#" + str(self.id) + ": " + self.status + ". To " + self.city + " at " + self.deadline


# A package-specific node class to be used by the hash_table class, as a node that points to other nodes.
class PkgNode:
    def __init__(self, pkg):
        self.pkg = pkg
        self.next = None

    def __str__(self):
        return "Pkg#" + str(self.pkg.id)


# A hash table with a given size
class PkgHashTable:
    def __init__(self, arr_size):
        self.arr_size = arr_size
        self.arr = [PkgNode(Package(-1, "", "", "", "", "", ""))]  # -1 is the sign of an empty bucket)
        for i in range(arr_size - 1):
            self.arr.append(PkgNode(Package(-1, "", "", "", "", "", "")))
        self.len = 0

    # Insert a new node onto the hash table
    def insert(self, id, address, city, zip, deadline, mass, status="At Warehouse"):
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

    # Insert a new node onto the hash table
    def remove(self, id):
        # Check if it exists on the table
        if self.lookup(id) is None:
            return

        # Find the node
        pkg_hash = id % self.arr_size
        node = self.arr[pkg_hash]
        prev_node = self.arr[pkg_hash]
        if node.pkg.id == id:                   # If it's first in the bucket, assign bucket to second node
            self.arr[pkg_hash] = node.next
            self.len -= 1
            return
        while node.next.pkg.id != id:
            node = node.next
        node.next = node.next.next              # Assign node.next to the node after the target
        self.len -= 1

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
        self.node = None

    # Figure out which package to return next
    def __next__(self):
        # Initialize node where needed
        if self.node is None:
            self.index = 0
            self.node = self.pkgs.arr[0]

        # Return the next node in the chain where available
        if self.node.next is not None:
            self.node = self.node.next
            return self.node.pkg

        # Loop through array until you find a valid node to return, or get to the last one
        while self.index < len(self.pkgs.arr) - 1:
            self.index += 1
            self.node = self.pkgs.arr[self.index]
            if self.node.pkg.id != -1:
                return self.node.pkg

        # Our node is in the last row, check to see if we're finished iterating
        if self.node.next is not None:
            self.node = self.node.next
            return self.node.pkg
        raise StopIteration


# A method that inserts package data into our hash table.
def load_pkgs(pkgs):
    pkgs.insert(1, "195 W Oakland Ave", "Salt Lake City", "84115", "10:30 AM", 21)
    pkgs.insert(2, "2530 S 500 E", "Salt Lake City", "84106", "EOD", 44)
    pkgs.insert(3, "233 Canyon Rd", "Salt Lake City", "84103", "EOD", 2)  # "Can only be on truck 2
    pkgs.insert(4, "380 W 2880 S", "Salt Lake City", "84115", "EOD", 4)
    pkgs.insert(5, "410 S State St", "Salt Lake City", "84111", "EOD", 5)
    pkgs.insert(6, "3060 Lester St", "West Valley City", "84119", "10:30 AM",
                88)  # "Delayed on flight---will not arrive to depot until 9:05 am
    pkgs.insert(7, "1330 2100 S", "Salt Lake City", "84106", "EOD", 8)
    pkgs.insert(8, "300 State St", "Salt Lake City", "84103", "EOD", 9)
    pkgs.insert(9, "300 State St", "Salt Lake City", "84103", "EOD", 2)  # "Wrong address listed
    pkgs.insert(10, "600 E 900 South", "Salt Lake City", "84105", "EOD", 1)
    pkgs.insert(11, "2600 Taylorsville Blvd", "Salt Lake City", "84118", "EOD", 1)
    pkgs.insert(12, "3575 W Valley Central Station bus Loop", "West Valley City", "84119", "EOD", 1)
    pkgs.insert(13, "2010 W 500 S", "Salt Lake City", "84104", "10:30 AM", 2)
    pkgs.insert(14, "4300 S 1300 E", "Millcreek", "84117", "10:30 AM", 88)  # "Must be delivered with 15, 19
    pkgs.insert(15, "4580 S 2300 E", "Holladay", "84117", "9:00 AM", 4)
    pkgs.insert(16, "4580 S 2300 E", "Holladay", "84117", "10:30 AM", 88)  # "Must be delivered with 13, 19
    pkgs.insert(17, "3148 S 1100 W", "Salt Lake City", "84119", "EOD", 2)
    pkgs.insert(18, "1488 4800 S", "Salt Lake City", "84123", "EOD", 6)  # "Can only be on truck 2
    pkgs.insert(19, "177 W Price Ave", "Salt Lake City", "84115", "EOD", 37)
    pkgs.insert(20, "3595 Main St", "Salt Lake City", "84115", "10:30 AM", 37)  # "Must be delivered with 13, 15
    pkgs.insert(21, "3595 Main St", "Salt Lake City", "84115", "EOD", 3)
    pkgs.insert(22, "6351 South 900 East", "Murray", "84121", "EOD", 2)
    pkgs.insert(23, "5100 South 2700 West", "Salt Lake City", "84118", "EOD", 5)
    pkgs.insert(24, "5025 State St", "Murray", "84107", "EOD", 7)
    pkgs.insert(25, "5383 South 900 East #104", "Salt Lake City", "84117", "10:30 AM",
                7)  # Delayed on flight---will not arrive to depot until 9:05 am
    pkgs.insert(26, "5383 South 900 East #104", "Salt Lake City", "84117", "EOD", 25)
    pkgs.insert(27, "1060 Dalton Ave S", "Salt Lake City", "84104", "EOD", 5)
    pkgs.insert(28, "2835 Main St", "Salt Lake City", "84115", "EOD",
                7)  # Delayed on flight---will not arrive to depot until 9:05 am
    pkgs.insert(29, "1330 2100 S", "Salt Lake City", "84106", "10:30 AM", 2)
    pkgs.insert(30, "300 State St", "Salt Lake City", "84103", "10:30 AM", 1)
    pkgs.insert(31, "3365 S 900 W", "Salt Lake City", "84119", "10:30 AM", 1)
    pkgs.insert(32, "3365 S 900 W", "Salt Lake City", "84119", "EOD",
                1)  # Delayed on flight---will not arrive to depot until 9:05 am
    pkgs.insert(33, "2530 S 500 E", "Salt Lake City", "84106", "EOD", 1)
    pkgs.insert(34, "4580 S 2300 E", "Holladay", "84117", "10:30 AM", 2)
    pkgs.insert(35, "1060 Dalton Ave S", "Salt Lake City", "84104", "EOD", 88)
    pkgs.insert(36, "2300 Parkway Blvd", "West Valley City", "84119", "EOD", 88)  # Can only be on truck 2
    pkgs.insert(37, "410 S State St", "Salt Lake City", "84111", "10:30 AM", 2)
    pkgs.insert(38, "410 S State St", "Salt Lake City", "84111", "EOD", 9)  # Can only be on truck 2
    pkgs.insert(39, "2010 W 500 S", "Salt Lake City", "84104", "EOD", 9)
    pkgs.insert(40, "380 W 2880 S", "Salt Lake City", "84115", "10:30 AM", 45)


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

    def to_string(self):
        return self.id + "\t" + self.name + "\t" + self.address


# A class containing a hash table of all locations, as well as an adjacency matrix
class Map:
    locations = {
        Location(0, "Western Governors University",
                 "4001 South 700 East, Salt Lake City, UT", "84107"),
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
        Location(16, "West Valley Prosecutor",
                 "3575 W Valley Central Station bus Loop", "84119"),
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
    }
    distances = [
        [0],
        [7.2, 0],
        [3.8, 7.1, 0],
        [11.0, 6.4, 9.2, 0],
        [2.2, 6.0, 4.4, 5.6, 0],
        [3.5, 4.8, 2.8, 6.9, 1.9, 0],
        [10.9, 1.6, 8.6, 8.6, 7.9, 6.3, 0],
        [8.6, 2.8, 6.3, 4.0, 5.1, 4.3, 4.0, 0],
        [7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0],
        [2.8, 6.3, 1.6, 7.3, 2.6, 1.5, 8.0, 9.3, 4.8, 0],
        [6.4, 7.3, 10.4, 1.0, 6.5, 8.7, 8.6, 4.6, 11.9, 9.4, 0],
        [3.2, 5.3, 3.0, 6.4, 1.5, 0.8, 6.9, 4.8, 4.7, 1.1, 7.3, 0],
        [7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0.6, 5.1, 12.0, 4.7, 0],
        [5.2, 3.0, 6.5, 3.9, 3.2, 3.9, 4.2, 1.6, 7.6, 4.6, 4.9, 3.5, 7.3, 0],
        [4.4, 4.6, 5.6, 4.3, 2.4, 3.0, 8.0, 3.3, 7.8, 3.7, 5.2, 2.6, 7.8, 1.3, 0],
        [3.7, 4.5, 5.8, 4.4, 2.7, 3.8, 5.8, 3.4, 6.6, 4.0, 5.4, 2.9, 6.6, 1.5, 0.6, 0],
        [7.6, 7.4, 5.7, 7.2, 1.4, 5.7, 7.2, 3.1, 7.2, 6.7, 8.1, 6.3, 7.2, 4.0, 6.4, 5.6, 0],
        [2.0, 6.0, 4.1, 5.3, 0.5, 1.9, 7.7, 5.1, 5.9, 2.3, 6.2, 1.2, 5.9, 3.2, 2.4, 1.6, 7.1, 0],
        [3.6, 5.0, 3.6, 6.0, 1.7, 1.1, 6.6, 4.6, 5.4, 1.8, 6.9, 1.0, 5.4, 3.0, 2.2, 1.7, 6.1, 1.6, 0],
        [6.5, 4.8, 4.3, 10.6, 6.5, 3.5, 3.2, 6.7, 1.0, 4.1, 11.5, 3.7, 1.0, 6.9, 6.8, 6.4, 7.2, 4.9, 4.4, 0],
        [1.9, 9.5, 3.3, 5.9, 3.2, 4.9, 11.2, 8.1, 8.5, 3.8, 6.9, 4.1, 8.5, 6.2, 5.3, 4.9, 10.6, 3.0, 4.6, 7.5, 0],
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
         13.1, 4.1, 4.7, 3.1, 7.8, 1.3, 8.3, 0]
    ]

    # Fill out the adjacency matrix for easier use later
    def __init__(self):
        for i in range(len(self.distances)):
            for j in range(len(self.distances)):
                try:
                    self.distances[i][j]
                except:
                    self.distances[i].append(self.distances[j][i])

    # Return a dictionary of indexes adjacent to the given location that map to distance away, sorted by distance
    def min_dist(self, x):
        adj_dict = {}
        for i in range(len(self.distances)):
            adj_dict[i] = self.distances[x][i]
        return sorted(adj_dict.items(), key=lambda x: x[1])

    # Looks up address and zip for a match, then returns a location id if a match is found
    @staticmethod
    def lookup(address, zip):
        for l in Map.locations:
            if l.zip == zip and l.address == address:
                return l.id
        return -1