# Author: Wesley Lancaster
# Date:   September 2020

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

from WGUPS_Objects import Truck, Package, PackageTable, Location, Map

# MAIN CLASS: Facilitates user interaction, and holds all instance data
# Instantiate all variables
trucks = {Truck(1), Truck(2)}
# TODO packages = PackageTable()


# TODO Temp testing
trucks[0].drive = 2.0
trucks[1].drive = 3.55
print(trucks[0].to_string())
print(trucks[1].to_string())