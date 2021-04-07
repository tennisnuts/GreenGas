'''
Author: Oliver Nunn
Date Modified: 8/2/2021

About:
    code to setup the station class for my 4yp project 'Green Gas'
'''

import numpy as np

# defining the station class and its methods
class Station:
    
    def __init__(self, electrolyser_capacity, station_capacity, storage_capacity):
        self.electrolyser_capacity = electrolyser_capacity
        self.station_capacity = station_capacity
        self.storage_capacity = storage_capacity
#    Separate parameters
        self.water_price = 1.9101/1000
        
    def get_optimised_electrolyser_demand(self, elec_price, dispenser_time_demand, starting_storage_level):
        '''
        Inputs:
            elec_price : numpy array of size 48 containing the half hourly electricity prices for that day.
            
            dispenser_time_demand : numpy array of varying size that contains (in order) the time at which each HGV
                                    is arriving i.e. for a HGV arriving at 2am, 10am and 6pm == [4,20,32].
                                    
            starting_storage_level : a number (float) that states how much Hydrogen there is at 00:00 before the 
                                     optimisation starts.
                                     
        Outputs:
            final_electrolyser_demand : numpy array of size 48 containing the optimised electrolyers demand for the 
                                        following 24 hrs.
                                        
            post_hgv_storage_level[z] : the ending storage level that can then be added into the stations self
                                        or input elsewhere.
        '''
        
        # Turns dispenser_time_demand into hydrogen demand
        dispenser_demand = np.zeros(48)
        for z in range(len(dispenser_time_demand)):
            dispenser_demand[dispenser_time_demand[z]] += 1
        dispenser_demand = dispenser_demand * 32.09
        
        # Initialises Vectors
        pre_hgv_storage_level = np.zeros(48)
        post_hgv_storage_level = np.zeros(48)
        final_electrolyser_demand = np.zeros(48)
        
        # Starts the Optimisation
        for z in range(48):

            # ____________________________________________________________________________
            # Loop for every z iteration
            # ____________________________________________________________________________

            electrolyser_demand = np.zeros(48)

            #Setting the Storage level for each hgv iteration
            if z == 0:
                storage_level = starting_storage_level
            else:
                storage_level = post_hgv_storage_level[z-1]



            for q in range(len(dispenser_time_demand)):

                # _______________________________________________________________________
                # Loop for every HGV
                # _______________________________________________________________________

                count = 0
                for k in range(len(dispenser_time_demand)):
                    if dispenser_time_demand[k] >= z:
                        count += 1

                temp = q-(len(dispenser_time_demand)-count)

                if temp >= 0:
                    h2_needed = max(((temp+1)*32.09 - storage_level),0)
                else:
                    h2_needed = 0



                small_array = elec_price[z:(dispenser_time_demand[q]+1)]
                sorted_small_array = np.argsort(small_array)

                for n in range(len(sorted_small_array)):
                    index = sorted_small_array[n] + z
                    if h2_needed > 0:
                        spare_capacity = min((self.electrolyser_capacity - electrolyser_demand[index]),(self.storage_capacity - storage_level))

                        if spare_capacity >= h2_needed:
                            electrolyser_demand[index] += h2_needed
                            storage_level += h2_needed
                            h2_needed = 0
                        if h2_needed > spare_capacity:
                            electrolyser_demand[index] += spare_capacity
                            storage_level += spare_capacity
                            h2_needed = h2_needed - spare_capacity


            final_electrolyser_demand[z] = electrolyser_demand[z]
            if z ==0:
                pre_hgv_storage_level[z] = starting_storage_level + electrolyser_demand[z]
            else:
                pre_hgv_storage_level[z] = post_hgv_storage_level[z-1] + electrolyser_demand[z]
            post_hgv_storage_level[z] = pre_hgv_storage_level[z] - dispenser_demand[z]
            
        return final_electrolyser_demand, pre_hgv_storage_level