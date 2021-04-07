import pandas as pd
import numpy as np
from random import choices
from collections import Counter


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

        hi = Counter(dispenser_time_demand)
        at_one_time = hi.most_common()[0][1]

    return final_electrolyser_demand, pre_hgv_storage_level, unsatisfied, at_one_time


def elec_prices_data(day):

    data = pd.read_csv("Data/agileprices2020.csv")
    temp = data.iloc[day - 1].values
    temp = temp[1::]

    return temp


def get_arrival_times(n_hgv):

    arrival_times = []

    population = [n for n in range(4, 48)]
    weights = []
    for n in range(len(population)):
        weights.append(1)

    for n in range(n_hgv):

        value = choices(population, weights)

        if value[0] == 4:
            weights[value[0] - 4] *= 0.1
            weights[value[0] - 3] *= 0.2
        if value[0] == 47:
            weights[value[0] - 4] *= 0.1
            weights[value[0] - 5] *= 0.2
        else:
            weights[value[0] - 4] *= 0.1
            weights[value[0] - 3] *= 0.2
            weights[value[0] - 5] *= 0.2

        arrival_times.append(value[0])

    arrival_times.sort()

    return arrival_times


"""
________________________________________________________________________________________________________
"""
"""
________________________________________________________________________________________________________
"""
"""
________________________________________________________________________________________________________
"""
"""
________________________________________________________________________________________________________
"""

total_COST_array = np.zeros(100)

for p in range(len(total_COST_array)):

    n_hgv = p + 1

    # if n_hgv <= 20:
    #     continue

    repayment_period = 7
    # print(n_hgv)

    array_arrival_times = np.zeros([365, n_hgv])
    for q in range(365):
        array_arrival_times[q] = get_arrival_times(n_hgv)
    array_arrival_times = array_arrival_times.astype(int)

    COST = np.zeros([5, 175])

    for i in range(len(COST)):
        # print(i)
        for j in range(len(COST[0])):

            print(n_hgv, i, j)

            n_electrolysers = i + 1
            n_canisters = j + 1

            electrolyser_capacity = n_electrolysers * 22.125
            storage_capacity = n_canisters * 9.5

            average_cost = np.zeros(365)
            unsatisfaction = np.zeros(365)
            max_at_one_time = np.zeros(365)
            for n in range(365):

                day = n + 1

                dispenser_time_demand = array_arrival_times[n].tolist()
                elec_price = elec_prices_data(day)
                starting_storage_level = 0

                (
                    demand,
                    level,
                    unsatisfied,
                    at_one_time,
                ) = get_optimised_electrolyser_demand(
                    elec_price,
                    dispenser_time_demand,
                    starting_storage_level,
                    electrolyser_capacity,
                    storage_capacity,
                )

                # convert from kg to kWh
                demand = demand * 51.38
                # convert to pounds
                elec_price = elec_price / 100

                cost = np.dot(demand, elec_price)

                average_cost[n] = cost / len(dispenser_time_demand)
                unsatisfaction[n] = unsatisfied
                max_at_one_time[n] = at_one_time

                if unsatisfied >= 1:
                    break

            yearly_avg_cost = np.average(average_cost)

            if np.sum(unsatisfaction) > 0:
                feasible = 0
            else:
                feasible = 1

            electrolyser_cost = 3475000 * n_electrolysers
            heat_exchanger_cost = 110000
            hydrogen_canister_cost = 24000 * n_canisters
            dispenser_cost = 90000 * np.max(max_at_one_time)
            hgv_cost = n_hgv * 55000

            capital_cost = (
                electrolyser_cost
                + heat_exchanger_cost
                + hydrogen_canister_cost
                + dispenser_cost
            )
            # yearly_return = (169.36 - yearly_avg_cost) * len(dispenser_time_demand) * 365

            price = (capital_cost) / (n_hgv * 365 * repayment_period) + yearly_avg_cost

            if feasible == 1:
                Price = price
            else:
                Price = 0

            COST[i][j] = Price

            df = pd.DataFrame(total_COST_array)
            df.to_csv("COST_Results_redo.csv")

            if j > 5:
                if COST[i][j - 1] > 0:
                    if COST[i][j] > COST[i][j - 1]:
                        break

    min_cost_array = []
    for i in range(len(COST)):
        for j in range(len(COST[0])):
            if COST[i][j] > 0:
                min_cost_array = np.append(min_cost_array, COST[i][j])

    print(np.min(min_cost_array))
    total_COST_array[p] = np.min(min_cost_array)

