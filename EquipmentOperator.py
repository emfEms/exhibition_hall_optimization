# coding=utf-8

from Config import *
import Data
import datetime


def get_close_time_schedule(elapsed_time):
    START = 0
    simulation_start = Data.simulation_period[START]
    next_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)

    print next_datetime

    # 다음 timestep의 외기 co2 값을 가져온다
    outdoor_co2 = Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == next_datetime]['CO2'].values[0]

    # 다음 timestep의 각 존 별 인원 수를 가져온다.
    zone_occupants_arrary = list()
    for zone in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
        column_id = 'ZONE-' + str(zone).zfill(2) + '-PEOPLECOUNT'
        peoplecount = Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == next_datetime][column_id].values[0]
        zone_occupants_arrary.append(peoplecount)

    # 제어값 도출
    zone_temperature_schedule_array = [EXHIBITION_HALL['return_temperature_setpoint_closed']] * EXHIBITION_HALL['number_of_ahu']
    ahu_on_off_schedule_array = [EXHIBITION_HALL['ahu_on_off_closed']] * EXHIBITION_HALL['number_of_ahu']
    ahu_coil_temperature_schedule_array = [EXHIBITION_HALL['ahu_coil_outlet_setpoint_closed']] * EXHIBITION_HALL['number_of_ahu']
    district_heating_temperature_schedule_array = [EXHIBITION_HALL['district_heating_setpoint_closed']] * EXHIBITION_HALL['number_of_district_heating']
    ahu_ventilation_on_off_schedule_array = [EXHIBITION_HALL['ahu_ventilation_on_off_closed']] * EXHIBITION_HALL['number_of_ahu']

    next_time_united_schedule_array = zone_temperature_schedule_array[:] + ahu_on_off_schedule_array[:] + zone_occupants_arrary[:] + [outdoor_co2]

    del zone_occupants_arrary
    del zone_temperature_schedule_array
    del ahu_on_off_schedule_array
    del ahu_coil_temperature_schedule_array
    del district_heating_temperature_schedule_array
    del ahu_ventilation_on_off_schedule_array

    return next_time_united_schedule_array


def get_open_time_schdule(IsInitialTargetTemperature, elapsed_time, control, planning):
    # 운영 계획 적용시 단위시간 만큼 유지
    if control is True and planning is False:
        Data.schedule_table.update_time_window()

    START = 0
    simulation_start = Data.simulation_period[START]
    next_datetime = simulation_start + datetime.timedelta(seconds=elapsed_time)

    # 다음 timestep의 외기 co2 값을 가져온다
    outdoor_co2 = Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == next_datetime]['CO2'].values[0]

    # 다음 timestep의 각 존 별 인원 수를 가져온다.
    zone_occupants_arrary = list()
    for zone in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
        column_id = 'ZONE-' + str(zone).zfill(2) + '-PEOPLECOUNT'
        peoplecount = Data.actual_occupants_outdoor_co2[Data.actual_occupants_outdoor_co2['DATETIME'] == next_datetime][column_id].values[0]
        zone_occupants_arrary.append(peoplecount)  ## 실제 재실인원 값을 가상환경으로 보내주어야 한다.
        # zone_occupants_arrary.append(0) ## default 값을 의미 원본재실인원


    # TODO: 설정 온도 및 습도에 의해 팬을 제어한다.
    zone_temperature_schedule_array = list()
    zone_ahu_onOff_schedule_array = list()
    ahu_on_off_schedule_array = list()
    ahu_coil_temperature_schedule_array = list()
    ahu_return_fan_temperature_schedule_array = list()
    ahu_ventilation_on_off_schedule_array = list()
    district_heating_temperature_schedule_array = list()

    for zone in range(1, EXHIBITION_HALL['number_of_zones'] + 1):
        # TODO: 존 설정온도를 가지고 온다 (현장에서 제어해야되는 온도)
        # zone_temperature_schedule_array.append(EXHIBITION_HALL['return_temperature_setpoint_opened'])

        zone_temperature_setpoint_id = 'ZONE-' + str(zone).zfill(2) + '-TEMPERATURE-SETPOINT'
        ahu_onoff_id = 'AHU-' + str(zone).zfill(2) + '-ON-OFF'


        zone_temperature_setpoint = Data.schedule_table.get_value(zone_temperature_setpoint_id, 0)
        ahu_on_off =  Data.schedule_table.get_value(ahu_onoff_id, 0)

        elapsed_hour = (float(elapsed_time % TIME_VARIABLE['day_in_seconds']) / float(TIME_VARIABLE['hour_in_seconds']))

        # print int(elapsed_hour)
        # if (int(elapsed_hour) == int(EXHIBITION_HALL['start_time_in_hour'])):
        #     zone_temperature_setpoint = EXHIBITION_HALL['return_temperature_setpoint_opened']

        zone_temperature_schedule_array.append(zone_temperature_setpoint)
        zone_ahu_onOff_id = 'AHU-' + str(zone).zfill(2) + '-ON-OFF'
        zone_ahu_onOff = Data.schedule_table.get_value(zone_ahu_onOff_id, 0)
        zone_ahu_onOff_schedule_array.append(zone_ahu_onOff)


        # TODO: energyplus output table에서 지난 타이밍 값을 가져온다
        variable_id = 'ZONE-' + str(zone).zfill(2) + '-TEMPERATURE'
        variable_index = [var['INDEX'] for var in Data.accumulation_table_variables if var['ID'] == variable_id][0]
        previous_zone_air_temperature = Data.previous_exhibition_hall_state[variable_index]

        ID = 'ZONE-' + str(zone).zfill(2) + '-CO2'
        variable_index = [var['INDEX'] for var in Data.accumulation_table_variables if var['ID'] == ID][0]
        previous_zone_co2 = Data.previous_exhibition_hall_state[variable_index]

        ahu_ventilation_on_off = eqiupment_on_off(previous_zone_co2, EXHIBITION_HALL['co2_upper_limit'])
        # ahu_on_off = winter_eqiupment_on_off(previous_zone_air_temperature, EXHIBITION_HALL['comfortable_temperature'])
        # ahu_on_off = summer_eqiupment_on_off(previous_zone_air_temperature, zone_temperature_setpoint)

        # if ahu_ventilation_on_off is True:
        #     ahu_on_off = True
        ahu_ventilation_on_off_schedule_array.append(ahu_ventilation_on_off)
        ahu_on_off_schedule_array.append(ahu_on_off)

    # TODO: 지역난방 설정온도를 가지고 온다

    # TODO: 지역난방, heating Coil의 setpoint는 제어대상이 아니기 때문에 default 값을 사용 한다

    next_time_united_schedule_array = zone_temperature_schedule_array[:] + ahu_on_off_schedule_array[:] + zone_occupants_arrary[:] + [outdoor_co2]

    del zone_occupants_arrary
    del zone_temperature_schedule_array
    del ahu_on_off_schedule_array
    del ahu_coil_temperature_schedule_array
    del district_heating_temperature_schedule_array
    del ahu_ventilation_on_off_schedule_array

    return next_time_united_schedule_array

def winter_eqiupment_on_off(previous_sensing_value, setpoint):
    if previous_sensing_value < setpoint:
        system_on_off = True
    else:
        system_on_off = False
    return system_on_off
def summer_eqiupment_on_off(previous_sensing_value, setpoint):
    if previous_sensing_value >= setpoint:
        system_on_off = True
    else:
        system_on_off = False
    return system_on_off
def temperature_trend(temperature):
    booking_list = list()
    for i in range(0, len(temperature)-1):
        if round(temperature[i], 1) > round(temperature[i+1], 1):
            booking_list.append(True)
        else:
            booking_list.append(False)
    return booking_list[:]

def reactive_operating(elapsed_time, eqiupment_on_off, past_sensing_temperature, previous_setpoint, delta_t):
    if is_control_interval(elapsed_time) is True:
        booking_list = temperature_trend(past_sensing_temperature)
        if eqiupment_on_off is True:
            if False in booking_list:
                next_time_setpoint = previous_setpoint - delta_t
                next_time_setpoint = min(max(float(CONTROLL_RANGE['setpoint_min']), next_time_setpoint), float(CONTROLL_RANGE['setpoint_max']))
            else:
                next_time_setpoint = previous_setpoint
        else:
            next_time_setpoint = previous_setpoint + delta_t
            next_time_setpoint = min(max(float(CONTROLL_RANGE['setpoint_min']), next_time_setpoint), float(CONTROLL_RANGE['setpoint_max']))
    else:
        next_time_setpoint = previous_setpoint

    return next_time_setpoint

def eqiupment_on_off(previous_sensing_value, setpoint):
    if previous_sensing_value >= setpoint:
        system_on_off = True
    else:
        system_on_off = False
    return system_on_off

def is_control_interval(elapsed_time):
    control = False
    if (elapsed_time % (SIMULATION_TIME_VARIABLE['control_interval_in_minutes'] * TIME_VARIABLE['minute_in_seconds'])) == 0:
        control = True
    return control

def generate_schedule_message(schedule_array):
    message = str()
    for schedule in schedule_array:
        one_of_schedule_value = "%f " % (float(schedule))
        message = message + one_of_schedule_value
    return message
