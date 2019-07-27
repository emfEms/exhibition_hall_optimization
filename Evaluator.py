# coding=utf-8
import json
from random import randrange
import numpy
from Config import *
from FilePath import *
import copy
# import EnergyCalCulator
import WinterEnergycalculator
from weka.core.dataset import Attribute, Instance, Instances
from weka.classifiers import Classifier
from weka.core.serialization import read
# from EnergyCalCulator import electricity
from WinterEnergycalculator import electricity
from WinterEnergycalculator import district_heat
import time

class Evaluator:
    def __init__(self, elapsed_time, simulation_table):
        self.elapsed_time = elapsed_time
        self.simulation_table_original = copy.deepcopy(simulation_table)
        #self.simulation_table = copy.deepcopy(simulation_table)
        self.simulation_table = None
        if simulation_table is None:
            raise AssertionError("simulation table의 인자가 주어지지 않았습니다.")

        # 인접 존의 평균 기온, 습도를 계산하기 위한 리스트 (zone 번호를 입력하면 인접 존 id 목록을 알려줌)
        self.adjacent_zones_temperature_list = None

        # individual decoding을 위한 리스트
        self.id_order_in_schedule = None
        with open(PATH_ADJACENT_ZONES_TEMPERATURE) as data_file:
            self.adjacent_zones_temperature_list = json.load(data_file)
        with open(PATH_ID_ORDER_IN_SCHEDULE) as data_file:
            self.id_order_in_schedule = json.load(data_file)

        # simulation model input attribute info 초기화
        self.input_attributes_outdoor_temperature = self.load_input_attributes_info(PATH_INPUT_ATTRIBUTES_OUTDOOR_TEMPERATURE)
        self.input_attributes_zone_temperature = list()
        for i in range(0, EXHIBITION_HALL['number_of_zones']):
            self.input_attributes_zone_temperature.append(self.load_input_attributes_info(PATH_INPUT_ATTRIBUTES_ZONE_TEMPERATURE[i]))
        self.input_attributes_energy = self.load_input_attributes_info(PATH_INPUT_ATTRIBUTES_ENERGY)

        self.input_attributes_district_heating = self.load_input_attributes_info(PATH_INPUT_ATTRIBUTES_DISTRICT_HEATING)

        # prediction model 초기화
        self.prediction_model_outdoor_temperature = self.load_prediction_model(PATH_PREDICTION_MODEL_OUTDOOR_TEMPERATURE)
        self.prediction_model_zone_temperature = list()
        for i in range(0, EXHIBITION_HALL['number_of_zones']):
            self.prediction_model_zone_temperature.append(self.load_prediction_model(PATH_PREDICTION_MODEL_ZONE_TEMPERATURE[i]))
        self.prediction_model_energy = self.load_prediction_model(PATH_PREDICTION_MODEL_ENERGY)
        self.prediction_model_district_heating = self.load_prediction_model(PATH_PREDICTION_MODEL_DISTRICT_HEATING)
        self.fitness = 0

        # weka에서 사용하기 위한 Instance set dictionary를 만들어 둔다
        # java bridge의 call 수를 줄이기 위함임
        self.weka_instance_set_dict = dict()

    def __del__(self):
        del self.simulation_table_original
        del self.simulation_table
        del self.adjacent_zones_temperature_list
        del self.id_order_in_schedule
        del self.input_attributes_outdoor_temperature
        del self.input_attributes_zone_temperature
        del self.input_attributes_energy
        del self.input_attributes_district_heating
        del self.prediction_model_outdoor_temperature
        del self.prediction_model_zone_temperature
        del self.prediction_model_energy
        del self.prediction_model_district_heating
        del self.weka_instance_set_dict



    # 최적화 알고리즘에서 제공하는 individual을 스케줄로 변환함
    # def decode_individual_to_schedule(self, individual, simulation_table):
    #     decoded_schedule = list()
    #     number_of_cotrolled_objects_in_timestep = len(self.id_order_in_schedule)
    #
    #     # 기본 생성되는 individual은 0~1사이 값을 가진다. 이를 -1~1 사이 값으로 변환시킨다
    #     new_individual = list()
    #     for i in range(0, len(individual)):
    #         new_individual.append((individual[i] - 0.5) * 2)
    #
    #     NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes']/SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
    #     NUMBER_OF_TIMESTEPS_IN_HORIZON_FIRST = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_first_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
    #     NUMBER_OF_TIMESTEPS_IN_HORIZON_SECOND = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_second_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_second_minutes'])
    #     for i in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON_FIRST):
    #         for j in range(0, EXHIBITION_HALL['number_of_zones']):
    #             if i == 0:  # t+1시점의 값은 이전 계획수립의 값으로 설정한다. simulation table에서 가져온다.
    #                 setpoint_id = self.id_order_in_schedule[j]
    #                 previous_temperature_setpoint = simulation_table.get_value(setpoint_id, i)
    #             else:  # t+2 이후 시점의 스케줄을 정한다. 이전 시점의 값은 decoded_schedule에서 가져온다
    #                 previous_temperature_setpoint_index = (i-1) * number_of_cotrolled_objects_in_timestep + j
    #                 previous_temperature_setpoint = decoded_schedule[previous_temperature_setpoint_index]
    #             temperature_delta = round(new_individual[i * number_of_cotrolled_objects_in_timestep + j], 1)
    #             temperature_setpoint = previous_temperature_setpoint + temperature_delta
    #             temperature_setpoint = max(min(temperature_setpoint, CONTROLL_RANGE["setpoint_max"]), CONTROLL_RANGE["setpoint_min"])
    #             decoded_schedule.append(temperature_setpoint)
    #         for j in range(EXHIBITION_HALL['number_of_zones'], number_of_cotrolled_objects_in_timestep):
    #             if i % 4 == 0:
    #                 onOff = randrange(0, 2)
    #             else:
    #                 previous_onOff_index = (i - 1) * number_of_cotrolled_objects_in_timestep + j
    #                 onOff = decoded_schedule[previous_onOff_index]
    #             ahu_OnOff = onOff
    #             decoded_schedule.append(ahu_OnOff)
    #     for i in range(NUMBER_OF_TIMESTEPS_IN_HORIZON_FIRST, NUMBER_OF_TIMESTEPS_IN_HORIZON_SECOND):
    #         for j in range(0, EXHIBITION_HALL['number_of_zones']):
    #             previous_temperature_setpoint_index = (i - 1) * number_of_cotrolled_objects_in_timestep + j
    #             previous_temperature_setpoint = decoded_schedule[previous_temperature_setpoint_index]
    #             temperature_delta = round(new_individual[i * number_of_cotrolled_objects_in_timestep + j], 1)
    #             temperature_setpoint = previous_temperature_setpoint + temperature_delta
    #             temperature_setpoint = max(min(temperature_setpoint, CONTROLL_RANGE["setpoint_max"]), CONTROLL_RANGE["setpoint_min"])
    #             decoded_schedule.append(temperature_setpoint)
    #
    #     for i in range(NUMBER_OF_TIMESTEPS_IN_HORIZON_SECOND, NUMBER_OF_TIMESTEPS_IN_HORIZON):
    #         previous_temperature_setpoint_index = (i - 1) * number_of_cotrolled_objects_in_timestep + j
    #         previous_temperature_setpoint = decoded_schedule[previous_temperature_setpoint_index]
    #         temperature_setpoint = previous_temperature_setpoint
    #         decoded_schedule.append(temperature_setpoint)
    #
    #
    #         for j in range(EXHIBITION_HALL['number_of_zones'],  EXHIBITION_HALL['number_of_zones'] + EXHIBITION_HALL['number_of_ahu']):
    #
    #             if i % 4 == 0:
    #             # else:  # t+2 이후 시점의 스케줄을 정한다. 이전 시점의 값은 decoded_schedule에서 가져온다
    #                 onOff = randrange(0, 2)
    #                 # previous_onOff_index = (i - 1) * number_of_cotrolled_objects_in_timestep + j
    #                 # onOff = decoded_schedule[previous_onOff_index]
    #             else :
    #                 previous_onOff_index = (i - 1) * number_of_cotrolled_objects_in_timestep + j
    #                 onOff = decoded_schedule[previous_onOff_index]
    #
    #             ahu_OnOff= onOff
    #             decoded_schedule.append(ahu_OnOff)
    #     # 불필요한 메모리 삭제
    #     del new_individual[:]
    #     return decoded_schedule

    def decode_schedules_to_simulation_schedule(self, candidate_schedules):
        simulation_schedules = list()
        FIRST_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_first_minutes'] / SIMULATION_TIME_VARIABLE['first_setpoint_control_interval_in_minutes'])
        NUMBER_OF_TIMESTEPS_IN_SETPOINT = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_first_minutes'] / SIMULATION_TIME_VARIABLE['first_setpoint_control_interval_in_minutes']) + \
                                          int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_second_minutes'] / SIMULATION_TIME_VARIABLE['second_setpoint_control_interval_in_minutes'])
        NUMBER_OF_TIMESTEPS_IN_ONOFF = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_ahu_on_off_minutes'] / SIMULATION_TIME_VARIABLE['on_off_control_interval_in_minutes'])

        for i in range(0, EXHIBITION_HALL['number_of_zones']):
            setpointlist = list()
            for j in range(0, FIRST_HORIZON):
                setpointlist.append(candidate_schedules[i][j])
            for m in range(FIRST_HORIZON, NUMBER_OF_TIMESTEPS_IN_SETPOINT):
                setpointlist.append(candidate_schedules[i][m])
                setpointlist.append(candidate_schedules[i][m])
                setpointlist.append(candidate_schedules[i][m])
                setpointlist.append(candidate_schedules[i][m])
            simulation_schedules.append(setpointlist)

        addindex =  EXHIBITION_HALL['number_of_zones']
        for i in range(addindex, addindex + EXHIBITION_HALL['number_of_zones']):
            onofflist = list()
            for j in range(0, NUMBER_OF_TIMESTEPS_IN_ONOFF):
                onofflist.append(candidate_schedules[i][j])
                # onofflist.append(candidate_schedules[i][j])
                # onofflist.append(candidate_schedules[i][j])
                # onofflist.append(candidate_schedules[i][j])
            simulation_schedules.append(onofflist)
        return simulation_schedules

    def decode_individual_to_schedules(self, individual, simulation_table, candidate_schedules):
        decoded_schedule = list()
        number_of_cotrolled_objects_in_timestep = len(self.id_order_in_schedule)
         # 기본 생성되는 individual은 0~1사이 값을 가진다. 이를 -1~1 사이 값으로 변환시킨다
        new_individual = list()
        for i in range(0, len(individual)):
            new_individual.append((individual[i] - 0.5) * 2)
        # print new_individual
        # print len(new_individual)
        NUMBER_OF_TIMESTEPS_IN_SETPOINT = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_first_minutes'] / SIMULATION_TIME_VARIABLE['first_setpoint_control_interval_in_minutes']) + \
                                          int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_setpoint_second_minutes'] / SIMULATION_TIME_VARIABLE['second_setpoint_control_interval_in_minutes'])
        NUMBER_OF_TIMESTEPS_IN_ONOFF = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_ahu_on_off_minutes'] / SIMULATION_TIME_VARIABLE['on_off_control_interval_in_minutes'])

        for i in range(0, EXHIBITION_HALL['number_of_zones']):
            setpointlist = list()
            for j in range(0, NUMBER_OF_TIMESTEPS_IN_SETPOINT):
                if j == 0:  # t+1시점의 값은 이전 계획수립의 값으로 설정한다. simulation table에서 가져온다.
                    setpoint_id = self.id_order_in_schedule[i]
                    previous_temperature_setpoint = simulation_table.get_value(setpoint_id, 0)
                else:  # t+2 이후 시점의 스케줄을 정한다. 이전 시점의 값은 decoded_schedule에서 가져온다
                    previous_temperature_setpoint_index = j - 1
                    previous_temperature_setpoint = setpointlist[previous_temperature_setpoint_index]
                temperature_delta = round(new_individual[(i * NUMBER_OF_TIMESTEPS_IN_SETPOINT) + j], 1)
                temperature_setpoint = previous_temperature_setpoint + temperature_delta
                temperature_setpoint = max(min(temperature_setpoint, CONTROLL_RANGE["setpoint_max"]), CONTROLL_RANGE["setpoint_min"])
                setpointlist.append(temperature_setpoint)
                # setpointlist.append(24.5)

            candidate_schedules.append(setpointlist)

        for i in range(0, EXHIBITION_HALL['number_of_zones']):
            onofflist = list()
            for j in range(0, NUMBER_OF_TIMESTEPS_IN_ONOFF):
                addindex = EXHIBITION_HALL['number_of_zones'] * NUMBER_OF_TIMESTEPS_IN_SETPOINT
                target_solution = new_individual[addindex + (i * NUMBER_OF_TIMESTEPS_IN_ONOFF) + j]
                on_off = 0
                if target_solution > 0:
                    on_off = 1

                #onofflist.append(on_off)
                onofflist.append(1)
            candidate_schedules.append(onofflist)
        # 불필요한 메모리 삭제
        del new_individual[:]

    # 스케줄을 시뮬레이션 테이블에 등록
    @classmethod
    def write_schedule_to_simulation_table(self, candidate_schedule, simulation_table):
        # schedule에 정의된 제어 대상들의 순서를 json 파일에서 읽어들인다
        # print len(candidate_schedule)
        with open(PATH_ID_ORDER_IN_SCHEDULE) as data_file:
            id_order_in_schedule = json.load(data_file)
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        ahu_on_id = 'TOTAL-AHU-ON'
        for i in range(0, len(id_order_in_schedule)):
            for j in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
                setpoint_id = id_order_in_schedule[i]
                value = candidate_schedule[i][j]
                simulation_table.set_value(setpoint_id, j+1, value)


        for i in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            total_ahu_on = 0
            for j in range(12, len(id_order_in_schedule)):
                value = candidate_schedule[j][i]
                total_ahu_on += value
            total_ahu_on = float(total_ahu_on)/EXHIBITION_HALL['number_of_ahu']
            simulation_table.set_value(ahu_on_id, i+1, total_ahu_on)

        # 불 필요한 메모리 삭제

        del id_order_in_schedule

    def evaluate(self, individual):
        # evaluate를 호출할 때마다 simulation table은 초기화된다
        self.simulation_table = copy.deepcopy(self.simulation_table_original)
        # print str(self.simulation_table)

        candidate_schedules = list()
        self.decode_individual_to_schedules(individual, self.simulation_table, candidate_schedules)
        simulation_schedules = self.decode_schedules_to_simulation_schedule(candidate_schedules)

        # candidate_schedule = self.decode_individual_to_schedule(individual, self.simulation_table)
        # schedule을 simulation attribute table에 등록한다.
        # self.write_schedule_to_simulation_table(candidate_schedule, self.simulation_table)
        self.write_schedule_to_simulation_table(simulation_schedules, self.simulation_table)

        # 시뮬레이션을 수행하여 평가값을 얻는다
        # start_time = time.time()
        #
        # print("start_time", start_time)  # 출력해보면, 시간형식이 사람이 읽기 힘든 일련번호형식입니다.

        self.fitness = self.do_simulation()
        # print("--- %s seconds ---" % (time.time() - start_time))

        # 불필요한 메모리 삭제
        del self.simulation_table
        del candidate_schedules[:]
        del simulation_schedules
        return self.fitness,


    def test_best_schedule(self, candidate_schedule):

        test = True
        # evaluate를 호출할 때마다 simulation table은 초기화된다
        self.simulation_table = copy.deepcopy(self.simulation_table_original)
        # print str(self.simulation_table)
        # candidate_schedule = self.decode_individual_to_schedule(individual, self.simulation_table)
        # schedule을 simulation attribute table에 등록한다.
        self.write_schedule_to_simulation_table(candidate_schedule, self.simulation_table)
        # 시뮬레이션을 수행하여 평가값을 얻는다
        # start_time = time.time()
        #
        # print("start_time", start_time)  # 출력해보면, 시간형식이 사람이 읽기 힘든 일련번호형식입니다.


        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        # 학습 모형에 필요한 현재 시간대 존 평균 온도, 습도, 전체 평균 온도 및 습도를 계산하여
        # simulation table에 갱신한다
        outdoorfile = open('outdoor.txt', 'a')
        outdoorfile.write(str(self.elapsed_time))
        outdoorfile.write('\n')

        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            self.simulate_outdoor_air_condition( current_time_step_index, outdoorfile, test)
            if current_time_step_index == NUMBER_OF_TIMESTEPS_IN_HORIZON - 1:
                outdoorfile.write('\n')
        outdoorfile.close()

        zonefileList = list()
        for i in range(1, 13) :
            zone_temp = 'zone_temp' + str(i) + '.txt'
            file = open(zone_temp, 'a')
            # file.write(str(self.elapsed_time))
            # file.write('\n')
            zonefileList.append(file)

        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            self.update_statistic_attributes_for_simulation( current_time_step_index)
            for target_zone_number in range(1, EXHIBITION_HALL['number_of_zones'] + 1):  # zone 번호는 1번부터 시작해야 한다
                self.simulate_zone_condition(target_zone_number, current_time_step_index, zonefileList[target_zone_number-1], test)
                if current_time_step_index == NUMBER_OF_TIMESTEPS_IN_HORIZON - 1:
                    zonefileList[target_zone_number - 1].write('\n')

            self.update_statistic_attributes_for_simulation( current_time_step_index + 1)
        for target in zonefileList:
            target.close()

        energyfile = open('electric.txt', 'a')
        energyfile.write(str(self.elapsed_time))
        energyfile.write('\n')
        coolingfile = open('cooling.txt', 'a')
        coolingfile.write(str(self.elapsed_time))
        coolingfile.write('\n')

        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            if current_time_step_index % 4 == 0:
                # print current_time_step_index
                self.simulate_energy_consumption( current_time_step_index, energyfile, test)
                self.simulate_district_heating_energy_consumption(current_time_step_index, coolingfile, test)
                if current_time_step_index == NUMBER_OF_TIMESTEPS_IN_HORIZON - 1:
                    energyfile.write('\n')
                    coolingfile.write('\n')
                # 시뮬레이션 수행 시 마지막 시간대의 존 평균 온도, 습도 등은 자동으로 갱신되지 않기 때문에
                # 수동으로 한 번 갱신해준다
        energyfile.close()
        coolingfile.close()

        f = open('penalty.txt', 'a')
        self.calculate_penalty_cost_log(self.elapsed_time,f)
        f.close()
        # print("--- %s seconds ---" % (time.time() - start_time))

        # 불필요한 메모리 삭제

        del zonefileList
        del outdoorfile
        del coolingfile
        del energyfile
        del self.simulation_table
        del candidate_schedule[:]
        return self.fitness,

    def do_simulation(self):
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        # 학습 모형에 필요한 현재 시간대 존 평균 온도, 습도, 전체 평균 온도 및 습도를 계산하여
        # simulation table에 갱신한다
        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            self.simulate_outdoor_air_condition(current_time_step_index, None, False)
        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            self.update_statistic_attributes_for_simulation(current_time_step_index)
            for target_zone_number in range(1, EXHIBITION_HALL['number_of_zones'] + 1):  # zone 번호는 1번부터 시작해야 한다
                self.simulate_zone_condition(target_zone_number, current_time_step_index, None, False)
            self.update_statistic_attributes_for_simulation(current_time_step_index+1)
        for current_time_step_index in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            if current_time_step_index % 4 == 0 :
                # print current_time_step_index
                self.simulate_energy_consumption(current_time_step_index, None, False)
                self.simulate_district_heating_energy_consumption(current_time_step_index, None, False)
        # 시뮬레이션 수행 시 마지막 시간대의 존 평균 온도, 습도 등은 자동으로 갱신되지 않기 때문에
        # 수동으로 한 번 갱신해준다



        """""""""
        # 전체 에너지 사용량을 계산한다. 에너지 사용량은 1시간 단위로만 예측이 가능하다
        NUMBER_OF_HOURS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / TIME_VARIABLE['hour_in_minutes'])
        NUMBER_OF_TIMESTEPS_PER_HOUR = int(TIME_VARIABLE['hour_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        for i in range(0, NUMBER_OF_HOURS_IN_HORIZON):
            current_time_step_index = i * NUMBER_OF_TIMESTEPS_PER_HOUR
            energy_consumption = self.predict(self.input_attributes_energy, self.prediction_model_energy, current_time_step_index)
            for j in range(0, NUMBER_OF_TIMESTEPS_PER_HOUR):
                energy_consumption_id = 'TOTAL-ENERGY-CONSUMPTION'
                energy_consumption_in_timestep = float(energy_consumption / float(NUMBER_OF_TIMESTEPS_PER_HOUR))
                self.simulation_table.set_value(energy_consumption_id, current_time_step_index + j + 1, energy_consumption_in_timestep)
        """""""""
        # 전력 가격을 적용해서 에너지 비용을 계산한다.
        energy_cost = self.calculate_energy_cost(self.elapsed_time)

        # 전시장 환경이 사용자 요구조건과 어긋나는 경우 패널티를 부여한다
        energy_cost += self.calculate_penalty_cost(self.elapsed_time)
        return energy_cost

    def update_statistic_attributes_for_simulation(self, current_time_step_index):
        self.update_zone_average_temperature(current_time_step_index)
        self.update_zone_average_peoplecount(current_time_step_index)
        for target_zone_number in range(1, EXHIBITION_HALL['number_of_zones']+1):
            self.update_adjacent_zone_temperature(target_zone_number, current_time_step_index)


    def simulate_outdoor_air_condition(self, current_time_step_index, file, test):
        next_time_step_index = current_time_step_index + 1
        # 외기 예측 모형을 이용해서 외기 상황을 예측한다
        outdoor_temperature = self.predict(self.input_attributes_outdoor_temperature,
                                           self.prediction_model_outdoor_temperature, current_time_step_index, file, test)
        # 외기 시뮬레이션 결과를 simulation variable table에 기록한다
        self.simulation_table.set_value('OUTDOOR-TEMPERATURE', next_time_step_index, outdoor_temperature)


    def simulate_zone_condition(self, target_zone_number, current_time_step_index, file, test):
        next_time_step_index = current_time_step_index + 1
        target_zone_string = str(target_zone_number).zfill(2)
        # 학습 모형을 이용해서 zone 환경에 대한 시뮬레이션을 수행한다
        zone_temperature = self.predict(self.input_attributes_zone_temperature[target_zone_number - 1],
                                        self.prediction_model_zone_temperature[target_zone_number - 1],
                                        current_time_step_index, file, test)



        # 현재는 재실인원 예측을 하지 않으므로 주석처리 하였음. 예측을 하는 경우 추가할 것
        # zone_people_count = 0
        # 존 별 시뮬레이션 결과를 simulation variable table에 기록한다
        zone_temperature_id = 'ZONE-' + target_zone_string + '-TEMPERATURE'
        total_ahu_on = 'ZONE-' + target_zone_string + '-PEOPLECOUNT'
        self.simulation_table.set_value(zone_temperature_id, next_time_step_index, zone_temperature)
        # self.simulation_table.set_value(zone_people_count_id, zone_people_count, next_time_step_index)



    def simulate_energy_consumption(self, current_time_step_index, file, test):
        next_time_step_index = current_time_step_index + 1
        # for i in range(0, len( self.input_attributes_energy)):
        #     print self.input_attributes_energy[i]
        energy_consumption = self.predict(self.input_attributes_energy, self.prediction_model_energy, current_time_step_index, file, test, True)
        energy_consumption_id = 'TOTAL-ENERGY-CONSUMPTION'
        for i in range (next_time_step_index, next_time_step_index + 4):
            self.simulation_table.set_value(energy_consumption_id, i, energy_consumption/4) ## 1시간동안의 에너지 사용량 합산이고, 현제프로그램은 15분단위이기 때문에 4로 나눈다.


    def simulate_district_heating_energy_consumption(self, current_time_step_index, file, test):
        next_time_step_index = current_time_step_index + 1
        district_heating_energy_consumption = self.predict(self.input_attributes_district_heating, self.prediction_model_district_heating, current_time_step_index, file, test, True)
        district_heating_energy_consumption_id = 'COOLING-AND-HEATING-ENERGY-CONSUMPTION'
        for i in range(next_time_step_index, next_time_step_index + 4):
            self.simulation_table.set_value(district_heating_energy_consumption_id, i, district_heating_energy_consumption/4)


    def predict(self, input_attributes_info, prediction_model, current_time_step_index, file, test, energy=False):
        # for i in range(0, len(input_attributes_info)):
        #    print input_attributes_info[i]

        # print current_time_step_index

        input_values = list()
        # input_attributes의 정보를 이용해서 simulation variable table로부터 예측에 필요한 입력값들을 가져옴
        for i in range(0, len(input_attributes_info)):
            # print input_attributes_info[i]
            value = 0
            # 속성 값이 simulation value table 내 특정 ID의 특정 Time step의 값인 경우
            if len(input_attributes_info[i]['TIME_STEP']) == 1:
                value = self.simulation_table.get_value(input_attributes_info[i]['ID'], input_attributes_info[i]['TIME_STEP'][0] + current_time_step_index)
                input_values.append(value)
            else:
                # 속성 값이 여러 time step의 값을 합산한 값으로 이루어진 경우 (예) 에너지 사용량 등)
                if input_attributes_info[i]['SUMMATION'] is True:
                    for j in range(0, len(input_attributes_info[i]['TIME_STEP'])):
                        value += self.simulation_table.get_value(input_attributes_info[i]['ID'], input_attributes_info[i]['TIME_STEP'][j] + current_time_step_index)
                    input_values.append(value)

                elif input_attributes_info[i]['AVERAGE'] is True:
                    for j in range(0, len(input_attributes_info[i]['TIME_STEP'])):
                        value += self.simulation_table.get_value(input_attributes_info[i]['ID'], input_attributes_info[i]['TIME_STEP'][j] + current_time_step_index)
                    value = value/float(len(input_attributes_info[i]['TIME_STEP']))
                    input_values.append(value)

                # 속성 값이 여러 time step의 값을 가진 경우 (예) 외기는 과거 15분, 30분 두가지를 반영함)
                else:
                    for j in range(0, len(input_attributes_info[i]['TIME_STEP'])):
                        value = self.simulation_table.get_value(input_attributes_info[i]['ID'], input_attributes_info[i]['TIME_STEP'][j] + current_time_step_index)
                        input_values.append(value)
        if test == True and energy == True :
             for val in input_values :
                testval = str(val)
                file.write(testval)
                file.write('  ')

        # 학습된 예측 모형을 이용해서 예측 수행
        instance = self.transfer_example_to_instance(input_values[:])
        prediction_result = Classifier(jobject=prediction_model).classify_instance(instance)
        if test == True:
            label = str(prediction_result)
            file.write(label)
            file.write('  ')
            if energy == True :
                file.write('\n')
        #불필요한 메모리 삭제
        # Instances.delete(instance)
        del input_values
        del instance


        return prediction_result


    #@profile()
    def transfer_example_to_instance(self, input_values):
        value_list = copy.deepcopy(input_values)
        # dimension을 맞추기 위해 dummy label 값을 추가한다
        value_list.append(-1)

        # Instance.new_instance()

        return Instance.create_instance(value_list)

    def load_prediction_model(self, path_prediction_model):
        return read(path_prediction_model)

    def update_zone_average_temperature(self, time_step):
        # 해당 time_step의 각 존의 온도를 불러들인다
        average_temperature = 0.0
        for zone_number in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
            zone_temperature_id = 'ZONE-' + str(zone_number).zfill(2) + '-TEMPERATURE'
            average_temperature += self.simulation_table.get_value(zone_temperature_id, time_step)
        average_temperature = average_temperature / float(EXHIBITION_HALL['number_of_zones'])
        average_temperature_id = 'ZONE-AVERAGE-TEMPERATURE'
        self.simulation_table.set_value(average_temperature_id, time_step, average_temperature)

    def update_adjacent_zone_temperature(self, target_zone_number, time_step):
        # 기온의 zone id는 1번 존의 경우 ZONE-01-TEMPERATURE이다
        zone_id = 'ZONE-' + str(target_zone_number).zfill(2) + '-ADJACENT-TEMPERATURE'
        adjacent_zone_list = self.adjacent_zones_temperature_list[zone_id]
        temperature = 0.0
        for id in adjacent_zone_list:
            temperature += self.simulation_table.get_value(id, time_step)
        temperature = temperature / float(len(adjacent_zone_list))
        self.simulation_table.set_value(zone_id, time_step, temperature)


    def calculate_energy_cost(self, current_time_in_seconds):
        cost = 0
        # TODO: 시스템 상 현재 시간이 언제인지 알아내는 코드 작성
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        CONTROL_INTERVAL_IN_SECONDS = int(SIMULATION_TIME_VARIABLE['control_interval_in_minutes'] * TIME_VARIABLE['minute_in_seconds'])
        for i in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            # 시뮬레이션 상의 시간을 계산한다
            current_time_in_seconds = current_time_in_seconds + CONTROL_INTERVAL_IN_SECONDS
            if current_time_in_seconds >= EXHIBITION_HALL['end_time_in_hour'] * TIME_VARIABLE['hour_in_seconds']:  # 17시 이후에는 가동을 하지 않으므로 비용을 계산하지 않음
                cost += 0
            else:
                # district_heating_energy_consumption_in_joule = self.simulation_table.get_value('COOLING-AND-HEATING-ENERGY-CONSUMPTION', i + 1)
                # # J 값을 kWh로 변환한다
                # district_heating_energy_consumption_in_in_kwh = district_heating_energy_consumption_in_joule / 3600000
                # # kWh 값을 Mcal로 변환한다
                # district_heating_energy_consumption_in_in_mcal = district_heating_energy_consumption_in_in_kwh * 0.0002388458966
                # # cost에 시간에 따른 distric_heating 비용을 더한다
                # district_heating_energy_consumption_time_step_cost = district_heat(current_time_in_seconds) * district_heating_energy_consumption_in_in_mcal

                cooling_and_heating_energy_consumption_in_joule = self.simulation_table.get_value('COOLING-AND-HEATING-ENERGY-CONSUMPTION', i + 1)
                cooling_and_heating_energy_consumption_in_kwh = cooling_and_heating_energy_consumption_in_joule / 3600000
                cooling_and_heating_energy_consumption_time_step_cost = electricity(current_time_in_seconds) * cooling_and_heating_energy_consumption_in_kwh

                cost += cooling_and_heating_energy_consumption_time_step_cost

                electric_energy_consumption_in_joule = self.simulation_table.get_value('TOTAL-ENERGY-CONSUMPTION', i + 1)
                # J 값을 kWh로 변환한다
                electric_energy_consumption_in_kwh = electric_energy_consumption_in_joule / 3600000
                # cost에 시간에 따른 electric 사용 비용을 더한다
                energy_consumption_time_step_cost = electricity(current_time_in_seconds) * electric_energy_consumption_in_kwh

                # print energy_consumption_time_step_cost
                cost += energy_consumption_time_step_cost
        return cost

    def load_input_attributes_info(self, path_input_attributes):
        with open(path_input_attributes) as data_file:
            input_attributes_info = json.load(data_file)
        return input_attributes_info

    def calculate_penalty_cost_log(self, current_time_in_seconds, f):
        # TODO: 적정 패널티 비용, 기온, 습도 상한의 조정
        penalty_cost = 0
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        for i in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            for zone_number in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
                target_zone_string = str(zone_number).zfill(2)
                zone_temperature_id = 'ZONE-' + target_zone_string + '-TEMPERATURE'
                # 각 존의 온/습도값을 가져온다
                zone_temperature = self.simulation_table.get_value(zone_temperature_id, i + 1)
                if zone_temperature > EXHIBITION_HALL['comfortable_temperature'] :
                    penalty_cost += 200000 * (zone_temperature - EXHIBITION_HALL['comfortable_temperature'])
                    penalty_cost += 20000 * (zone_temperature) - EXHIBITION_HALL['district_heating_setpoint_closed']

        logpenaly = str(penalty_cost)
        f.write(logpenaly)
        f.write(' ')
        return penalty_cost
    def calculate_penalty_cost(self, current_time_in_seconds):
        # TODO: 적정 패널티 비용, 기온, 습도 상한의 조정
        penalty_cost = 0
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        for i in range(0, NUMBER_OF_TIMESTEPS_IN_HORIZON):
            is_give_penalty = False
            for zone_number in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
                target_zone_string = str(zone_number).zfill(2)
                zone_temperature_id = 'ZONE-' + target_zone_string + '-TEMPERATURE'
                # 각 존의 온/습도값을 가져온다
                zone_temperature = self.simulation_table.get_value(zone_temperature_id, i + 1)
                if zone_temperature > EXHIBITION_HALL['comfortable_temperature']:
                    penalty_cost += 200000 * (zone_temperature - EXHIBITION_HALL['comfortable_temperature'])
                elif zone_temperature > EXHIBITION_HALL['penalty_temperature']:
                    penalty_cost += 32.3 * (zone_temperature - EXHIBITION_HALL['penalty_temperature'])


        return penalty_cost
    def update_zone_average_peoplecount(self, current_time_step_index):
        # 해당 time_step의 각 존의 온도를 불러들인다
        average_peoplecount = 0.0
        for zone_number in range(1, EXHIBITION_HALL['number_of_zones']+1):
            humidity_id = 'ZONE-' + str(zone_number).zfill(2) + '-PEOPLECOUNT'
            average_peoplecount += self.simulation_table.get_value(humidity_id, current_time_step_index)
        average_peoplecount = average_peoplecount / float(EXHIBITION_HALL['number_of_zones'])
        average_people_id = 'ZONE-AVERAGE-PEOPLECOUNT'
        self.simulation_table.set_value(average_people_id, current_time_step_index, average_peoplecount)