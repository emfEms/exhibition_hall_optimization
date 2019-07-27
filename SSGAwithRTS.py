# coding=utf-8
'''
Created on 2016. 7. 29.

@author: birdzero
'''
import time
from deap import base, creator, tools
import math
import random
from Evaluator import Evaluator
from Config import *
import copy

def getDistance(ind1, ind2):
    sum = 0
    for i in range(len(ind1)):
        sum += pow(ind1[i] - ind2[i], 2)

    return math.sqrt(sum)

def findMostSimilarInd(population, ind):
    most_similar = 0
    best_distance = getDistance(population[0], ind)
    count = len(population)
    for i in range(1, count):
        cur_distance = getDistance(population[i], ind)
        if (cur_distance < best_distance):
            most_similar = i
            best_distance = cur_distance
    return population[most_similar]


def MainProcess(elapsed_time, simulation_table):
    start_time = time.time()
    IND_SIZE = (EXHIBITION_HALL['number_of_zones']) * \
               (int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_first_minutes']/SIMULATION_TIME_VARIABLE['first_setpoint_control_interval_in_minutes']) + \
               int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_second_minutes']/SIMULATION_TIME_VARIABLE['second_setpoint_control_interval_in_minutes']) + \
               int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_ahu_on_off_minutes'] / SIMULATION_TIME_VARIABLE['on_off_control_interval_in_minutes']))
    POP_SIZE = 50
    NEVAL = 5000
    # crossover parameter
    CXPB = 1
    CXETA = 1
    CXLOW = 0
    CXUP = 1
    # mutation parameter
    MUTPB = 1
    MUTETA = 1
    MUTLOW = 0
    MUTUP = 1
    INDPB = 0.2
    # RTS parameter
    MAT_POOL_SIZE = 2
    REP_POOL_SIZE = 5

    evaluator = Evaluator(elapsed_time, simulation_table)
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("attribute", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attribute, n=IND_SIZE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("mate", tools.cxSimulatedBinaryBounded, eta=CXETA, low=CXLOW, up=CXUP)
    toolbox.register("mutate", tools.mutPolynomialBounded, eta=MUTETA, low=MUTLOW, up=MUTUP, indpb=INDPB)
    toolbox.register("select", tools.selRandom)
    toolbox.register("evaluate", evaluator.evaluate)
    toolbox.register("test_best_schedule", evaluator.test_best_schedule)

    population = toolbox.population(n=POP_SIZE)
    fits = toolbox.map(toolbox.evaluate, population)
    for fit, ind in zip(fits, population):
        ind.fitness.values = fit

    for g in range(0, NEVAL, 2):
        # Select the next generation individuals
        parents = toolbox.select(population, MAT_POOL_SIZE)

        # Clone the selected individuals
        offsprings = [toolbox.clone(ind) for ind in parents]

        # Apply crossover on the offspring
        for child1, child2 in zip(offsprings[::2], offsprings[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # Apply mutation on the offspring
        for mutant in offsprings:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        for ind in offsprings:
            ind.fitness.values = toolbox.evaluate(ind)

        # Restricted Tournament Selection
        for offspring in offsprings:
            replace_pool = toolbox.select(population, REP_POOL_SIZE)
            most_similar = findMostSimilarInd(replace_pool, offspring)
            if (offspring.fitness.values[0] < most_similar.fitness.values[0]):
                population.remove(most_similar)
                population.append(offspring)
        del replace_pool
        del most_similar
        del offsprings
        del parents
    best = None
    for pop in population:
        if best is None:
            best = pop
        else:
            if pop.fitness.values[0] < best.fitness.values[0]:
                best = pop

    end_time = time.time()

    opt_schedules = list()
    evaluator.decode_individual_to_schedules(best, simulation_table, opt_schedules)
    optimal_schedules = evaluator.decode_schedules_to_simulation_schedule(opt_schedules)

    # optimal_schedule = evaluator.decode_individual_to_schedule(best, simulation_table)

    # outFile = open('elapsed_time_for_optimize.txt', 'a')
    # outFile.write('Schedule Time: %.05f\n' % (elapsed_time))
    # outFile.write('Running Time: %.05f\n' % (end_time - start_time))
    # PrintList = ['AHU1', 'AHU2', 'AHU3', 'AHU4', 'AHU5', 'AHU6','AHU7', 'AHU8', 'AHU9', 'AHU10', 'AHU11', 'AHU12']
    # valueList = list()
    # for i in range(0, EXHIBITION_HALL['number_of_ahu']):
    #     s = PrintList[i] + ': '
    #     for j in range(0, int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])):
    #         valueList.append(round(optimal_schedules[j * (EXHIBITION_HALL['number_of_ahu']) + i ], 1))
    #     s = s + str(valueList)
    #     outFile.write(s + '\n')
    #     del valueList[:]
    # outFile.close()

    test = copy.copy(optimal_schedules)
    toolbox.test_best_schedule(test)
    # 불 필요한 메모리 삭제
    del evaluator
    del toolbox
    del population
    del fits
    # del valueList[:]
    # del PrintList
    # del outFile
    return optimal_schedules
