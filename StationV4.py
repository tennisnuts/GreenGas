'''
Author: Oliver Nunn
Date Modified: 8/2/2021

About:
    code to setup the station class for my 4yp project 'Green Gas'
    
Change:
    putting in the electrolyser size and canisters size optimisation into the station so that no inputs are needed to 
    set up the station - the optimisation just needs to be run
'''

import numpy as np
import Prices
from collections import Counter
import math

# defining the station class and its methods
class Station:
    
    def __init__(self):
        
#    Separate parameters
        self.water_price = 1.9101/1000
        
    def get_optimised_electrolyser_demand(self, elec_price, dispenser_time_demand, starting_storage_level,electrolyser_capacity,storage_capacity):
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
        
        # determines if the demand can be met
        unsatisfied = 0
        
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
                        spare_capacity = min((electrolyser_capacity - electrolyser_demand[index]),(storage_capacity - storage_level))

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
            
            if post_hgv_storage_level[z] < 0:
                unsatisfied += 1
            
            post_hgv_storage_level[z] = max(post_hgv_storage_level[z],0)
            pre_hgv_storage_level[z] = max(pre_hgv_storage_level[z],0)
            
        return final_electrolyser_demand, pre_hgv_storage_level, unsatisfied
    
    def get_min_parameters(self, dispenser_time_demand):
        # the number below is set at 1 initially but the optimisation will increase this until the conditions are satisfied
        number_electorlysers = 1

        # --------------------
        # making sure the while loop can start
        unsatisfaction = np.array([1])
        # --------------------
        '''
        ------------------------------------------------------------------------------------------------------------
        '''



        # ----------------------------------------------------------------------------------------------------------
        # running a while loop to get the minimum number of canisters and the minimum number of electrolysers
        # ----------------------------------------------------------------------------------------------------------
        while np.sum(unsatisfaction) > 0:
            '''
            ------------------------------------------------------------------------------------------------------------
            work out the minimum number of canisters to satisfy the demand at the end of the half hour period
            '''
            counter = Counter(dispenser_time_demand)
            temp = np.zeros(49)
            for n in range(49):
                temp[n] = counter[n]
            temp2 = np.argsort(temp)[-1]
            maximum = counter[temp2]
            min_number_canisters = math.ceil((maximum*32.09)/9.5)
            number_canisters = min_number_canisters
            '''
            -------------------------------------------------------------------------------------------------------------
            '''



            '''
            -------------------------------------------------------------------------------------------------------------
            work out the minimum number of canisters to satisfy the constraint that the station needs to be able to charge
            and discharge at the same time
            '''
            spare_capacity = number_canisters*9.5-maximum*32.09
            charge_time = (spare_capacity)/(0.0123*number_electorlysers)
            discharge_time = 9.5/0.0382
            while discharge_time > charge_time:
                number_canisters += 1
                spare_capacity = number_canisters*9.5-maximum*32.09
                charge_time = (spare_capacity)/(0.0123*number_electorlysers)
                discharge_time = 9.5/0.0382
            '''
            -------------------------------------------------------------------------------------------------------------
            '''






            '''
            -------------------------------------------------------------------------------------------------------------
            set up the station with its parameters
            '''

            electrolyser_capacity = 22.125*number_electorlysers

            storage_capacity = 9.5*number_canisters


            '''
            -------------------------------------------------------------------------------------------------------------
            '''



            '''
            -------------------------------------------------------------------------------------------------------------
            run the system for 2020 price data
            '''
            total_cost = np.zeros(365)
            unsatisfaction = np.zeros(365)

            for n in range(365):

                day = n+1
                elec_price = Prices.elec_prices_data(day)

                starting_storage_level = 0

                demand, level, unsatisfied = self.get_optimised_electrolyser_demand(elec_price, dispenser_time_demand, starting_storage_level,electrolyser_capacity,storage_capacity)

                # convert from demand in kg to kWh
                demand = demand*49.465
                # convert electricity prices into pounds
                elec_price = elec_price/100
                # find the cost of the refill
                cost = np.dot(demand,elec_price)

                total_cost[n] = cost
                unsatisfaction[n] = unsatisfied
            '''
            -------------------------------------------------------------------------------------------------------------
            '''




            '''
            -------------------------------------------------------------------------------------------------------------
            work out the average refill cost
            '''
            avg_refill_cost = (np.average(total_cost))/(len(dispenser_time_demand))
            '''
            -------------------------------------------------------------------------------------------------------------
            '''




            '''
            -------------------------------------------------------------------------------------------------------------
            if any HGV's were unsatisfied then increment the number of electrolysers and run the simulation again
            '''
            if np.sum(unsatisfaction) > 0:
                number_electorlysers += 1
            '''
            -------------------------------------------------------------------------------------------------------------
            '''
        # ----------------------------------------------------------------------------------------------------------
        # running a while loop to get the minimum number of canisters and the minimum number of electrolysers
        # ----------------------------------------------------------------------------------------------------------
        self.n_electrolysers = number_electorlysers
        self.n_canisters = number_canisters
        
        self.electrolyser_capacity = 22.125*self.n_electrolysers
        self.storage_capacity = 9.5*self.n_canisters