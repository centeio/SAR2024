import numpy as np
import math


# task name : [distance, flooded]

tasks = {"A": [0.2,0.2], "B": [0.2,0.8], "C": [0.8,0.2], "D": [0.8,0.8]}
total_tasks = 12


def calculate_weights(task_sequence):
    weights = np.array([0.0,0.0])
    sum_ranks = np.array([0.0,0.0])
    counter = np.array([0.0,0.0])

    t_i = 0

    # for each task performed by the agent
    for task in task_sequence:
        # for each task characteristic update the reward weight
        for w_i in range(len(weights)):
            if t_i > 0:
                if tasks[task_sequence[t_i]][w_i] == tasks[task_sequence[t_i - 1]][w_i]:
                    counter[w_i] = 0
                else:
                    counter[w_i] = 0

            #print("counter", counter)
           
            characteristic_i = tasks[task][w_i] # task characteristic: 0 or 1
            rank = (t_i + 1) - counter[w_i] 
            weight = characteristic_i * rank

            # print("w_i: ", w_i , " task: ", task, " characteristic: " , characteristic_i, " rank: ", rank, " weight: ", weight)

            # if characteristic is 1, then we add the rank of the position of the first consecutive characteristic to weight
            weights[w_i] = weights[w_i] + weight
            # print("weights: ", weights) 
            sum_ranks[w_i] += t_i + 1
        
        
        t_i += 1

    # normalize the weights
    weights = weights / sum_ranks

    print("weights: ", weights)
    return weights

def calculate_reward(task_c_list, weights):
    reward = 0
    for i in range(len(task_c_list)):
        # print("task_c_list: ", task_c_list[i], " weight_list: ", weights[i])
        reward -= task_c_list[i] * weights[i]

    return reward

def calculate_tasks_reward(task_sequence):
    weights = calculate_weights(task_sequence)
    tasks_reward = {}
    for task in tasks:
        reward = calculate_reward(tasks[task], weights)
        tasks_reward[task] = reward

    return tasks_reward

if __name__ == "__main__":

    print("Tasks reward ABCD: ", calculate_tasks_reward(["A", "A", "A", "B", "B", "B", "C", "C", "C", "D", "D", "D"]))
    print("Tasks reward ACBD: ", calculate_tasks_reward(["A", "A", "A",  "C", "C", "C", "B", "B", "B", "D", "D", "D"]))
    print("Tasks reward DCBA: ", calculate_tasks_reward(["D", "D", "D", "C", "C", "C", "A", "A", "A", "B", "B", "B"]))


    print("Tasks reward ABCD rotation: ", calculate_tasks_reward(["A","B","C","D","A","B","C","D","A","B","C","D","A","B","C","D"]))
    #print("Tasks reward AB: ", calculate_tasks_reward(["A","A","A","B","B","B"]))







