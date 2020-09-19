from datetime import time

# A class that represents a Truck object, with
#   id (int)
#   route (list of ints)
#   packages (list of ints that each represent a package in the package hash table)
#   time (datetime)
#   miles (double)
class Truck:
    # Ctor, start time at 8
    def __init__(self, id, packages):
        self.id = id
        self.time = time(8)
        self.speed = 18     #miles per hour
        self.max_packages = 16     #max amount of packages

    @property
    def packages(self):
        return self.packages
    @packages.setter
    def packages(self, list):
        if list.length > self.max_packages:
            # TODO throw Exception("Trucks cannot carry this many packages!")
            return


    # Drive the truck (adds time and mileage)
    def drive(self, miles):
        self.miles += miles
        self.time = self.time + time(miles * 18)

    # Truck info in one string
    def to_string(self):
        return "Truck " + id + " at " + self.time + ": " + self.miles + "miles"

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
    def __init__(self, id, destination, deadline, mass, truck, pkg_group, arrival_time, delivery_time):
        self.id = id
        self.destination = destination
        self.deadline = deadline
        self.mass = mass
        self.truck = truck
        self.pkg_group = pkg_group
        self.arrival_time = arrival_time

class PackageTable:
    def __init__(self):
        return {

        }


# A class that represents a location to deliver a package to, with
#   id (int)
#   name (string)
#   address (string)
class Location:
    def __init__(self, id, name, address):
        self.id = id
        self.name = name
        self.address = address
    def to_string(self):
        return self.id + "\t" + self.name + "\t" + self.address

# A class containing a hash table of all locations, as well as an adjacency matrix
class Map:
    def __init__(self):
        locations ={
            Location( 0, "Western Governors University",
                      "4001 South 700 East, Salt Lake City, UT 84107"),
            Location( 1, "International Peace Gardens",                 "1060 Dalton Ave S 84104"),
            Location( 2, "Sugar House Park",                            "1330 2100 S 84106"),
            Location( 3, "Taylorsville-Bennion Heritage City Gov Off",  "1488 4800 S 84123"),
            Location( 4, "Salt Lake City Division of Health Services",  "177 W Price Ave 84115"),
            Location( 5, "South Salt Lake Public Works",                "195 W Oakland Ave 84115"),
            Location( 6, "Salt Lake City Streets and Sanitation",       "2010 W 500 S 84104"),
            Location( 7, "Deker Lake",                                  "2300 Parkway Blvd 84119"),
            Location( 8, "Salt Lake City Ottinger Hall",                "233 Canyon Rd 84103"),
            Location( 9, "Columbus Library",	                        "2530 S 500 E 84106"),
            Location(10, "Taylorsville City Hall",                      "2600 Taylorsville Blvd 84118"),
            Location(11, "South Salt Lake Police",                      "2835 Main St 84115"),
            Location(12, "Council Hall",               	                "300 State St(84103)"),
            Location(13, "Redwood Park",             	                "3060 Lester St(84119)"),
            Location(14, "Salt Lake County Mental Health",	            "3148 S 1100 W(84119)"),
            Location(15, "Salt Lake County/United Police Dept",	        "3365 S 900 W(84119)"),
            Location(16, "West Valley Prosecutor",
                     "3575 W Valley Central Station bus Loop(84119)"),
            Location(17, "Housing Auth. of Salt Lake County",	        "3595 Main St(84115)"),
            Location(18, "Utah DMV Administrative Office",	            "380 W 2880 S(84115)"),
            Location(19, "Third District Juvenile Court",	            "410 S State St(84111)"),
            Location(20, "Cottonwood Regional Softball Complex",	    "4300 S 1300 E(84117)"),
            Location(21, "Holiday City Office",	                        "4580 S 2300 E(84117)"),
            Location(22, "Murray City Museum",	                        "5025 State St(84107)"),
            Location(23, "Valley Regional Softball Complex",	        "5100 South 2700 West(84118)"),
            Location(24, "City Center of Rock Springs",	                "5383 S 900 East #104(84117)"),
            Location(25, "Rice Terrace Pavilion Park",	                "600 E 900 South(84105)"),
            Location(26, "Wheeler Historic Farm",	                    "6351 South 900 East(84121)")
        }
        self.distances = {
            {0},
            {7.2, 0},
            {3.8, 7.1, 0},
            {11.0, 6.4, 9.2, 0},
            {2.2, 6.0, 4.4, 5.6, 0},
            {3.5, 4.8, 2.8, 6.9, 1.9, 0},
            {10.9, 1.6, 8.6, 8.6, 7.9, 6.3, 0},
            {8.6, 2.8, 6.3, 4.0, 5.1, 4.3, 4.0, 0},
            {7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0},
            {2.8, 6.3, 1.6, 7.3, 2.6, 1.5, 8.0, 9.3, 4.8, 0},
            {6.4, 7.3, 10.4, 1.0, 6.5, 8.7, 8.6, 4.6, 11.9, 9.4, 0},
            {3.2, 5.3, 3.0, 6.4, 1.5, 0.8, 6.9, 4.8, 4.7, 1.1, 7.3, 0},
            {7.6, 4.8, 5.3, 11.1, 7.5, 4.5, 4.2, 7.7, 0.6, 5.1, 12.0, 4.7, 0},
            {5.2, 3.0, 6.5, 3.9, 3.2, 3.9, 4.2, 1.6, 7.6, 4.6, 4.9, 3.5, 7.3, 0},
            {4.4, 4.6, 5.6, 4.3, 2.4, 3.0, 8.0, 3.3, 7.8, 3.7, 5.2, 2.6, 7.8, 1.3, 0},
            {3.7, 4.5, 5.8, 4.4, 2.7, 3.8, 5.8, 3.4, 6.6, 4.0, 5.4, 2.9, 6.6, 1.5, 0.6, 0},
            {7.6, 7.4, 5.7, 7.2, 1.4, 5.7, 7.2, 3.1, 7.2, 6.7, 8.1, 6.3, 7.2, 4.0, 6.4, 5.6, 0},
            {2.0, 6.0, 4.1, 5.3, 0.5, 1.9, 7.7, 5.1, 5.9, 2.3, 6.2, 1.2, 5.9, 3.2, 2.4, 1.6, 7.1, 0},
            {3.6, 5.0, 3.6, 6.0, 1.7, 1.1, 6.6, 4.6, 5.4, 1.8, 6.9, 1.0, 5.4, 3.0, 2.2, 1.7, 6.1, 1.6, 0},
            {6.5, 4.8, 4.3, 10.6, 6.5, 3.5, 3.2, 6.7, 1.0, 4.1, 11.5, 3.7, 1.0, 6.9, 6.8, 6.4, 7.2, 4.9, 4.4, 0},
            {1.9, 9.5, 3.3, 5.9, 3.2, 4.9, 11.2, 8.1, 8.5, 3.8, 6.9, 4.1, 8.5, 6.2, 5.3, 4.9, 10.6, 3.0, 4.6, 7.5, 0},
            {3.4, 10.9, 5.0, 7.4, 5.2, 6.9, 12.7, 10.4, 10.3, 5.8, 8.3, 6.2, 10.3, 8.2, 7.4, 6.9, 12.0, 5.0, 6.6, 9.3,
             2.0, 0},
            {2.4, 8.3, 6.1, 4.7, 2.5, 4.2, 10.0, 7.8, 7.8, 4.3, 4.1, 3.4, 7.8, 5.5, 4.6, 4.2, 9.4, 2.3, 3.9, 6.8, 2.9,
             4.4, 0},
            {6.4, 6.9, 9.7, 0.6, 6.0, 9.0, 8.2, 4.2, 11.5, 7.8, 0.4, 6.9, 11.5, 4.4, 4.8, 5.6, 7.5, 5.5, 6.5, 11.4, 6.4,
             7.9, 4.5, 0},
            {2.4, 10.0, 6.1, 6.4, 4.2, 5.9, 11.7, 9.5, 9.5, 4.8, 4.9, 5.2, 9.5, 7.2, 6.3, 5.9, 11.1, 4.0, 5.6, 8.5, 2.8,
             3.4, 1.7, 5.4, 0},
            {5.0, 4.4, 2.8, 10.1, 5.4, 3.5, 5.1, 6.2, 2.8, 3.2, 11.0, 3.7, 2.8, 6.4, 6.5, 5.7, 6.2, 5.1, 4.3, 1.8, 6.0,
             7.9, 6.8, 10.6, 7.0, 0},
            {3.6, 13.0, 7.4, 10.1, 5.5, 7.2, 14.2, 10.7, 14.1, 6.0, 6.8, 6.4, 14.1, 10.5, 8.8, 8.4, 13.6, 5.2, 6.9,
             13.1, 4.1, 4.7, 3.1, 7.8, 1.3, 8.3, 0}
        }
    @property
    def distances(self, x, y):
        if x > y:
            return self.distances[y][x]
        return self.distances[x][y]