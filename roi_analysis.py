import pandas as pd
import numpy as np


def get_optimised_electrolyser_demand(
    elec_price,
    dispenser_time_demand,
    starting_storage_level,
    electrolyser_capacity,
    storage_capacity,
):
    """
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
    """

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

        # Setting the Storage level for each hgv iteration
        if z == 0:
            storage_level = starting_storage_level
        else:
            storage_level = post_hgv_storage_level[z - 1]

        for q in range(len(dispenser_time_demand)):

            # _______________________________________________________________________
            # Loop for every HGV
            # _______________________________________________________________________

            count = 0
            for k in range(len(dispenser_time_demand)):
                if dispenser_time_demand[k] >= z:
                    count += 1

            temp = q - (len(dispenser_time_demand) - count)

            if temp >= 0:
                h2_needed = max(((temp + 1) * 32.09 - storage_level), 0)
            else:
                h2_needed = 0

            small_array = elec_price[z : (dispenser_time_demand[q] + 1)]
            sorted_small_array = np.argsort(small_array)

            for n in range(len(sorted_small_array)):
                index = sorted_small_array[n] + z
                if h2_needed > 0:
                    spare_capacity = min(
                        (electrolyser_capacity - electrolyser_demand[index]),
                        (storage_capacity - storage_level),
                    )

                    if spare_capacity >= h2_needed:
                        electrolyser_demand[index] += h2_needed
                        storage_level += h2_needed
                        h2_needed = 0
                    if h2_needed > spare_capacity:
                        electrolyser_demand[index] += spare_capacity
                        storage_level += spare_capacity
                        h2_needed = h2_needed - spare_capacity

        final_electrolyser_demand[z] = electrolyser_demand[z]
        if z == 0:
            pre_hgv_storage_level[z] = starting_storage_level + electrolyser_demand[z]
        else:
            pre_hgv_storage_level[z] = (
                post_hgv_storage_level[z - 1] + electrolyser_demand[z]
            )
        post_hgv_storage_level[z] = pre_hgv_storage_level[z] - dispenser_demand[z]

        if post_hgv_storage_level[z] < 0:
            unsatisfied += 1

        post_hgv_storage_level[z] = max(post_hgv_storage_level[z], 0)
        pre_hgv_storage_level[z] = max(pre_hgv_storage_level[z], 0)

    return final_electrolyser_demand, pre_hgv_storage_level, unsatisfied


def elec_prices_data(day):

    data = pd.read_csv("Data/agileprices2020.csv")
    temp = data.iloc[day - 1].values
    temp = temp[1::]

    return temp


"""
_______________________________________________________________________________________________________________________________
"""

"""
_______________________________________________________________________________________________________________________________
"""
"""
_______________________________________________________________________________________________________________________________
"""

"""
_______________________________________________________________________________________________________________________________
"""

dispenser_time_demand = [4]
starting_storage_level = 0
electrolyser_capacity = 22.125 * 1
storage_capacity = 9.5 * 4

arrival_time_cost = np.zeros(48)
for i in range(4, 48):
    print(i)
    dispenser_time_demand = [i]
    """
    Yearly simulation
    """
    daily_refill_avg = np.zeros(365)
    for n in range(365):

        day = n + 1

        elec_price = elec_prices_data(day)

        demand, level, unsatisfied = get_optimised_electrolyser_demand(
            elec_price,
            dispenser_time_demand,
            starting_storage_level,
            electrolyser_capacity,
            storage_capacity,
        )

        if unsatisfied > 0:
            print("Unsatisfied")

        elec_demand = demand * 51.38  # kWh

        refill_cost = np.dot(elec_demand, elec_price / 100)

        avg_refill_cost = refill_cost / len(dispenser_time_demand)

        daily_refill_avg[n] = avg_refill_cost

    arrival_time_cost[i] = np.average(daily_refill_avg)

df = pd.DataFrame(arrival_time_cost)
df.to_csv("Results.csv")

