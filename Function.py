# coding=utf-8
from Config import *
import datetime
import pandas
import json
from pyidf import idf
import Data
import random



def upload_data_to_table(elapsed_time, exhibition, planning):

    # 누적테이블 저장 매시간 마다 데이터 기록
    Data.accumulation_table.shift()
    Data.accumulation_table.update_time_window()
    for var in Data.accumulation_table_variables:
        var_name = var["ID"]
        var_index = var["INDEX"]
        Data.accumulation_table.set_value(var_name, 0, Data.previous_exhibition_hall_state[var_index])


    if exhibition is True and planning is True:
        #schedule_table 데이터 삭제
        Data.schedule_table.clear()
        #simulation table 데이터 삭제
        Data.simulation_table.clear()
        # 누적테이블의 데이터를 종합하여 시뮬레이션 테이블에 저장
        # 제어 단위 5분 외기온도 과거 30분 반영을 위한 시뮬레이션 테이블 width = 행 6칸 + 운영 계획 길이
        # 제어 단위 15분 외기온도 과거 30분 반영을 위한 시뮬레이션 테이블 width = 행 2칸 + 운영 계획 길이
        # 제어 단위 30분 외기온도 과거 30분 반영을 위한 시뮬레이션 테이블 width = 행 1칸 + 운영 계획 길이

        #평균이 필요한 편수
        avg_variables = [variable for variable in Data.simulation_table_variables if variable['SET'] == 'AVG']
        control_width = int(SIMULATION_TIME_VARIABLE['control_interval_in_minutes']/SIMULATION_TIME_VARIABLE['time_step_in_minutes'])
        for variable in avg_variables:
            simulation_table_time_index = 0
            for accumulation_table_time_index in range(Data.accumulation_table.time_window_max_width-1, Data.accumulation_table.time_window_start_index-1, -control_width):
                sum = 0
                for j in range(0, control_width):
                    sum = sum + Data.accumulation_table.get_value(variable['ID'], -(accumulation_table_time_index-j))
                average = sum / control_width
                Data.simulation_table.set_value(variable['ID'], simulation_table_time_index, average)
                simulation_table_time_index = simulation_table_time_index + 1

        #합산이 필요한 변수
        sum_variables = [variable for variable in Data.simulation_table_variables if variable['SET'] == 'SUM']
        for variable in sum_variables:
            simulation_table_time_index = 0
            for accumulation_table_time_index in range(Data.accumulation_table.time_window_max_width-1, Data.accumulation_table.time_window_start_index-1, -control_width):
                sum = 0
                for j in range(0, control_width):
                    sum = sum + Data.accumulation_table.get_value(variable['ID'], -(accumulation_table_time_index-j))
                Data.simulation_table.set_value(variable['ID'], simulation_table_time_index, sum)
                # print simulation_table_time_index
                simulation_table_time_index = simulation_table_time_index + 1

        #과거 데이터 정리 후 simultion table time index시점 현재로 변환
        Data.simulation_table.time_window_current_index = int(SIMULATION_TIME_VARIABLE['past_horizon_width_in_minutes']/SIMULATION_TIME_VARIABLE['control_interval_in_minutes']) - 1

        # predicted environment data로부터 예보와 관련된 정보를 읽어들인다
        START = 0
        simulation_start = Data.simulation_period[START]
        current_hour = int(elapsed_time / TIME_VARIABLE['hour_in_seconds'])%24
        try:
            current_datetime = simulation_start.replace(hour=current_hour)
        except ValueError:
            current_datetime += datetime.timedelta(hours=24)

        # 현재 시점을 기준으로 예보값을 가져온다
        temperature_t1t4 = Data.forecast[Data.forecast['DATETIME'] == current_datetime]['TEMPERATURE-T1T4'].values[0]
        temperature_t4t7 = Data.forecast[Data.forecast['DATETIME'] == current_datetime]['TEMPERATURE-T4T7'].values[0]

        # 현재 예보의 시작 시점을 계산한다.  0시 -> 0시, 1시 -> 0시, 2시 -> 0시, 3시 -> 3시, 4시 -> 3시, 5시 -> 3시...
        forecast_base_hour = current_hour - (current_hour % 3)
        t1t4_end_time_in_seconds = forecast_base_hour * TIME_VARIABLE['hour_in_seconds'] + 3 * TIME_VARIABLE['hour_in_seconds']
        # 현재 시각이 t1t4의 end_time을 경과한 경우 t4t7 예보값을 적용한다

        # list 구성: 온도 예보(0~3h), 온도 예보(3~6h), 습도 예보(0~3h), 습도 예보(3~6h), CO2, 12개 존 재실 인원
        NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
        CONTROL_INTERVAL_IN_SECONDS = SIMULATION_TIME_VARIABLE['control_interval_in_minutes'] * TIME_VARIABLE['minute_in_seconds']
        for time_step in range(1, NUMBER_OF_TIMESTEPS_IN_HORIZON + 1):
            elapsed_time_in_simulation = elapsed_time + (CONTROL_INTERVAL_IN_SECONDS * time_step)
            is_using_first_forecast = elapsed_time_in_simulation <= t1t4_end_time_in_seconds
            if is_using_first_forecast is True:
                Data.simulation_table.set_value('OUTDOOR-TEMPERATURE-FORECAST', time_step, temperature_t1t4)
            else:
                Data.simulation_table.set_value('OUTDOOR-TEMPERATURE-FORECAST', time_step, temperature_t4t7)


        # 과거 1시간을 포함한 시간대별 재실인원 예측값을 받아온다.
        past_horizon = int(SIMULATION_TIME_VARIABLE['past_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes']) - 1
        for time_step in range(-past_horizon, NUMBER_OF_TIMESTEPS_IN_HORIZON + 1):
            for zone in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
                column_id = 'ZONE-' + str(zone).zfill(2) + '-PEOPLECOUNT'
                if time_step < 0:  # 과거시점이면 실측 재실인원값을 가져온다
                    new_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)
                    minutes = abs(time_step) * SIMULATION_TIME_VARIABLE['control_interval_in_minutes']
                    new_datetime = new_datetime - datetime.timedelta(minutes=minutes)
                    peoplecount =   Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == new_datetime][column_id].values[0]
                    Data.simulation_table.set_value(column_id, time_step, peoplecount)

                else:
                    new_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)
                    minutes = time_step * SIMULATION_TIME_VARIABLE['control_interval_in_minutes']
                    new_datetime = new_datetime + datetime.timedelta(minutes=minutes)
                    peoplecount =   Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == new_datetime][column_id].values[0]
                    peoplecount = int(generate_error(peoplecount))
                    Data.simulation_table.set_value(column_id, time_step, peoplecount)


        # simulation variable table에 저장된 값 average type 변수들의 값을 계산한다
        average_variables = [(Data.simulation_table_variables[i]['ID'], Data.simulation_table_variables[i]['Dependency']) for i in
                             range(0, len(Data.simulation_table_variables)) if Data.simulation_table_variables[i]['Type'] == "Average"]

        for variable, dependency in average_variables:
            for time_step in range(-past_horizon, 1):
                average_value = 0
                for ID in dependency:
                    average_value += Data.simulation_table.get_value(ID, time_step)
                average_value = float(average_value) / float(len(dependency))
                Data.simulation_table.set_value(variable, time_step, average_value)

        # 전체 에너지 사용량을 계산한다.
        composite_variables = [(Data.simulation_table_variables[i]['ID'], Data.simulation_table_variables[i]['Dependency'])
                               for i in range(0, len(Data.simulation_table_variables)) if Data.simulation_table_variables[i]['Type'] == "Composite"]
        for variable, dependency in composite_variables:
            for time_step in range(-past_horizon, 1):
                ahu_energy = 0
                chiller_energy = 0
                for ID in dependency:
                    if ID.find('ENERGY') != -1:
                        ahu_energy += Data.simulation_table.get_value(ID, time_step)
                    elif ID.find('AHU') != -1 and ID.find('CALOMETER') != -1:
                        chiller_energy += Data.simulation_table.get_value(ID, time_step)
                    else:
                        continue
                Data.simulation_table.set_value(variable, time_step, ahu_energy + chiller_energy)
        #메모리 삭제
        del avg_variables[:], average_variables[:], sum_variables[:], composite_variables[:]


def write_schedule_to_schedule_table(simulation_table, schedule_table, simulation_table_variables):

    schedule_variables = [simulation_table_variables[i]['ID'] for i in range(0, len(simulation_table_variables))
                          if simulation_table_variables[i]['Type'] == "Schedule"]

    # simulation table에 있는 t+1 시점의 값부터 차례대로 schdeule_table에 기록한다.
    NUMBER_OF_TIMESTEPS_IN_HORIZON = int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
    for time_step in range(1, NUMBER_OF_TIMESTEPS_IN_HORIZON + 1):
        for ID in schedule_variables:
            value = simulation_table.get_value(ID, time_step)
            schedule_table.set_value(ID, time_step-1, value)
    # 불필요한 메모리 삭제
    del schedule_variables


def get_simulation_period(idf_filename):
    idf_file = idf.IDF(idf_filename)
    run_period_name = 'Run Period 1'
    run_period = list((c for c in idf_file.runperiods if c.name == run_period_name))[0]
    begin_year = 2017
    begin_month = run_period.begin_month
    begin_day = run_period.begin_day_of_month
    end_year = 2017
    end_month = run_period.end_month
    end_day = run_period.end_day_of_month
    string_start = '%d-%d-%d %d:%d:%d' % (begin_year, begin_month, begin_day, 0, 0, 0)
    start = datetime.datetime.strptime(string_start, '%Y-%m-%d %H:%M:%S')
    string_end = '%d-%d-%d %d:%d:%d' % (end_year, end_month, end_day, 23, 59, 59)
    end = datetime.datetime.strptime(string_end, '%Y-%m-%d %H:%M:%S')

    print start
    return [start, end]

def figure_out_exhibition_situation(elapsed_time):
    exhibition = False
    planning = False
    control = False
    elapsed_time = elapsed_time % 86400
    if (elapsed_time >= EXHIBITION_HALL['start_time_in_hour'] * TIME_VARIABLE['hour_in_seconds']) \
            and (elapsed_time < EXHIBITION_HALL['end_time_in_hour'] * TIME_VARIABLE['hour_in_seconds']):
        exhibition = True
    if elapsed_time % (SIMULATION_TIME_VARIABLE['control_interval_in_minutes'] * TIME_VARIABLE['minute_in_seconds']) == 0:
        control = True
    if elapsed_time % (SIMULATION_TIME_VARIABLE['planning_interval_in_minutes'] * TIME_VARIABLE['minute_in_seconds']) == 0:
        planning = True
    return exhibition, control, planning

def generate_error(value):
    error = value * (random.random() * 0.1)
    if (random.choice([True, False])):
        val = value + error
    else:
        val = value - error
    return val


def translate_client_message(client_message):
    TIME_INDEX = 0
    EXHIBITION_HALL_STATE_INDEX = 1
    message_element = client_message.split('|')
    elapsed_time = float(message_element[TIME_INDEX])
    str_exhibition_hall_state = message_element[EXHIBITION_HALL_STATE_INDEX]
    str_exhibition_hall_state = str_exhibition_hall_state[0:len(str_exhibition_hall_state)].replace('[', '')
    str_exhibition_hall_state = str_exhibition_hall_state[0:len(str_exhibition_hall_state)].replace(']', '')
    list_str_exhibition_hall_state = str_exhibition_hall_state.split(';')
    #list_str_exhibition_hall_state.pop()
    exhibition_hall_state = [float(i) for i in list_str_exhibition_hall_state]

    #메모리삭제
    del message_element, str_exhibition_hall_state, list_str_exhibition_hall_state
    return elapsed_time, exhibition_hall_state[:]

def read_csv_file_with_datetime_to_dataframe(filename, datetime_column_name):
    datetime_column_list = list()
    datetime_column_list.append(datetime_column_name)
    string_circumstance_data = pandas.read_csv(filename, parse_dates=datetime_column_list)
    return string_circumstance_data


def write_json_file(json_data, filename):
    with open(filename, "w") as data_file:
        json.dump(json_data, data_file, indent=2, ensure_ascii=False)


def read_json_file(filename):
    # type: (object) -> object
    with open(filename) as data_file:
        return json.load(data_file)