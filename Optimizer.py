# coding=utf-8
import sys
import os
from Function import *
from Config import *
from FilePath import *
from EquipmentOperator import get_close_time_schedule, get_open_time_schdule, generate_schedule_message
from VariableTableManager import VariableTableManager
from SSGAwithRTS import MainProcess
from Evaluator import Evaluator
import weka.core.jvm as jvm
import Data
import TCPManager
import copy
import time
import cPickle
import zmq
import pickle
import time


class TcpConnect:
    def __init__(self):

        # communicator의 ip and port
        self.server_ip = "tcp://127.0.0.1:%s"
        self.port = "5555"
        self.context = None
        self.socket = None

        # communicator의 ip and port
        self.model_server_ip = "tcp://127.0.0.1:%s"
        self.model_port = "5555"
        self.model_context = None
        self.model_socket = None

    def people_count_model(self):
        self.model_context = zmq.Context()
        print "Connecting to predict_model..."
        self.model_socket = self.model_context.socket(zmq.REQ)
        self.model_socket.connect(self.model_server_ip % self.model_port)

    def setPeopleCount(self, elapsed_time):
        print 'setPeopleCount'
        zone_occupants_arrary = self.setPreviousPeopleCount(elapsed_time)
        self.setForecastPeopleCount(zone_occupants_arrary)

    def setForecastPeopleCount(self, zone_occupants_arrary):

        print 'setForecastPeopleCount'
        start_time = time.time()
        f = open ('people_count.txt', 'a')
        f.write(str(elapsed_time))
        print zone_occupants_arrary
        self.model_socket.send((pickle.dumps(zone_occupants_arrary)))
        outputs = cPickle.loads(self.model_socket.recv())
        print("--- PC model : %s seconds ---" % (time.time() - start_time))
        # f2.write(str(self.hours))

        Data.predicted_Occupants = list()
        for time_step in range(1, 13):
            f.write('\n')
            f.write('time step : ')
            for zone in range(1, EXHIBITION_HALL['number_of_zones']+1):
                value = outputs[time_step-1][zone-1]
                id = 'ZONE-' + str(zone).zfill(2) + '-PEOPLECOUNT'
                f.write(str(value))
                f.write(', ')
            Data.simulation_table.set_value(id, time_step, value)
            # Data.predicted_Occupants.append(zoneOccupants) ## [3,4,5,6,1,2,3,1,1,1,1,5], [...], [...], ... (5분 ~ 60분후까지) 각타이밍 별로 12개의존의 재실인원이 들어간다.
            f.write('\n')
        f.close()
        del outputs
        del zone_occupants_arrary
        del f
        # print  Data.predicted_Occupants

    def setPreviousPeopleCount(self, elapsed_time):

        zone_occupants_arrary = list()
        print elapsed_time
        simulation_start = Data.simulation_period[0]
        next_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)
        print simulation_start + datetime.timedelta(seconds=float(elapsed_time))

        for zone in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
            column_id = 'ZONE-' + str(zone).zfill(2) + '-PEOPLECOUNT'
            zone_input = list()
            one_step = 300 ## 300seconds
            for time_step in range(-11, 1):  # timestep 길이만큼 재실인원값을 읽어옴 (3시간전부터 현제까지)
                target_datetime = str(simulation_start+ datetime.timedelta(seconds=float(elapsed_time) + (time_step * one_step)))
                peoplecount = Data.simulation_table.get_value(column_id, time_step)
                # peoplecount = Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == target_datetime][column_id].values[0] # 실제과거 재실인원 데이터를 읽어온다
                peoplecount = int(round(float(peoplecount)))
                zone_input.append(peoplecount)
            zone_occupants_arrary.append(zone_input)

        return zone_occupants_arrary

    def set_peopleCountOfSimulationTable(self, elapsed_time):
        Data.predicted_Occupants = None
        self.people_count_model()  # 재실인원 예측모델과 연결
        self.setPeopleCount(elapsed_time)  # -3~11(1시간전에서 3시간후) 까지의 1~12번 zone의 재실인원수를 시뮬레이션 테이블에 채운다
        # self.setAveragePeopleCount()  # -3~0(1시간전에서 현제) 까지의 평균재실인원수를 시뮬레이션 테이블에 채운다


def add_base_occupants(actual_occupants_outdoor_co2, additional_base_occupants):
    df = actual_occupants_outdoor_co2.filter(regex="PEOPLE").astype(float, copy=False)
    df = df.add(additional_base_occupants)
    print(df)
    df = df.astype('str')
    actual_occupants_outdoor_co2.update(df)
    return actual_occupants_outdoor_co2


if __name__ == '__main__':
    start_time = time.time()
    # jvm은 프로그램 시작시 켜고, 종료 시 끈다
    IsInitialTargetTemperature = False
    optimizer = TcpConnect()
    jvm.start()
    tcp_manager = TCPManager.TCPManager()
    tcp_manager.set_server("5556")
    working_directory = os.getcwd()
    Data.simulation_period = get_simulation_period(process_filepath)
    Data.accumulation_table_variables = read_json_file(accumulation_table_variables_filepath)
    Data.simulation_table_variables = read_json_file(simulation_table_variables_filepath)
    Data.schedule_table_variables = [{'ID': Data.simulation_table_variables[i]['ID']} for i in range(0, len(Data.simulation_table_variables))
                                     if Data.simulation_table_variables[i]['Type'] == "Schedule"]

    Data.accumulation_table = VariableTableManager(Data.accumulation_table_variables, TABLE_SIZE_VARIABLE['accumulation_table_size'])
    Data.simulation_table = VariableTableManager(Data.simulation_table_variables, TABLE_SIZE_VARIABLE['simulation_table_size'])
    Data.schedule_table = VariableTableManager(Data.simulation_table_variables, TABLE_SIZE_VARIABLE['schedule_table_size'])

    Data.actual_occupants_outdoor_co2 = read_csv_file_with_datetime_to_dataframe(actual_exhibition_hall_circumstance_filepath, 'DATETIME')
    additional_base_occupants = 200
    Data.actual_occupants_outdoor_co2 = add_base_occupants(Data.actual_occupants_outdoor_co2, additional_base_occupants)
    Data.forecast = read_csv_file_with_datetime_to_dataframe(forecast_filepath, 'DATETIME')

    logTime = open('logTime.txt', 'a')
    while True:

        start_time = time.time()
        print(start_time)
        tcp_manager.receive()
        client_message = tcp_manager.return_message()
        print(client_message)
        elapsed_time, previous_exhibition_hall_state = translate_client_message(client_message)
        # print elapsed_time
        exhibition, control, planning = figure_out_exhibition_situation(elapsed_time)
        Data.previous_exhibition_hall_state = copy.copy(previous_exhibition_hall_state[:])


        if elapsed_time > 0:
            current_AVG_temperature = upload_data_to_table(elapsed_time, exhibition, planning)

        if exhibition is True and planning is True:
            # 계획을 수립한다.
            if (float(elapsed_time) % 3600) == 0:
                optimizer.set_peopleCountOfSimulationTable(elapsed_time)

            best = MainProcess(elapsed_time, Data.simulation_table)
            # 기록의 편의를 위해 schdeule 값을 simulation table에 저장한다.
            # Evaluator.evaluate2(best, Data.simulation_table)
            Evaluator.write_schedule_to_simulation_table(best, Data.simulation_table)
            # 가져온 스케줄을 schedule table에 저장한다.
            write_schedule_to_schedule_table(Data.simulation_table, Data.schedule_table, Data.simulation_table_variables)
            low_level_schdule = get_open_time_schdule(IsInitialTargetTemperature, elapsed_time, control, planning)
            logTime.write("--- : %s seconds ---" % (time.time() - start_time))
            logTime.write('\n')
        elif exhibition is True and planning is False:

            low_level_schdule = get_open_time_schdule(IsInitialTargetTemperature, elapsed_time, control, planning)
        else:
            low_level_schdule = get_close_time_schedule(elapsed_time)

        message = generate_schedule_message(low_level_schdule)
        tcp_manager.send(message)
        print message
        START = 0
        simulation_start = Data.simulation_period[START]
        next_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)

        if elapsed_time % 900 == 0 :
            logTime.write("%s 제어계획: %s"  % (next_datetime, message))
            logTime.write('\n')
            logTime.write('\n')

        # 운영 계획 수립중 불필요한 메모리 삭제
        del client_message
        del Data.previous_exhibition_hall_state[:], previous_exhibition_hall_state[:]
        del low_level_schdule[:]
        del message

    #프로그램 종료시 불필요한 메모리 삭제
    del Data.simulation_period
    del Data.accumulation_table_variables
    del Data.simulation_table_variables
    del Data.schedule_table_variables
    del Data.accumulation_table
    del Data.simulation_table
    del Data.schedule_table
    del Data.actual_occupants_outdoor_co2
    del Data.forecast
    del Data.predicted_occupants
    logTime.close()
    print "complete"
    jvm.stop()
    print("start_time", start_time)  # 출력해보면, 시간형식이 사람이 읽기 힘든 일련번호형식입니다.
    print("--- %s seconds ---" % (time.time() - start_time))
