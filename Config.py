# coding=utf-8
# 운영 모드

# 시간 정의
TIME_VARIABLE = {
    'minute_in_seconds': 60,
    'hour_in_seconds': 60*60,
    'hour_in_minutes': 60,
    'day_in_seconds': 86400
}

SIMULATION_TIME_VARIABLE = {
    'time_step_in_minutes': 5,
    'past_horizon_width_in_minutes': 180,
    'schedule_horizon_width_in_minutes': 180,

    'schedule_horizon_width_in_setpoint_first_minutes': 60,
    'schedule_horizon_width_in_setpoint_second_minutes': 120,
    'first_setpoint_control_interval_in_minutes': 15,
    'second_setpoint_control_interval_in_minutes': 60,

    'schedule_horizon_width_in_ahu_on_off_minutes': 180,
    'on_off_control_interval_in_minutes': 15,


    'control_interval_in_minutes': 15,

    'planning_interval_in_minutes': 60
}

TABLE_SIZE_VARIABLE = {
    'accumulation_table_size': int(SIMULATION_TIME_VARIABLE['past_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['time_step_in_minutes']),
    'simulation_table_size': int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes']) +12,# 재실인원 3시간전까지 필요함
    'schedule_table_size': int(SIMULATION_TIME_VARIABLE['schedule_horizon_width_in_minutes'] / SIMULATION_TIME_VARIABLE['control_interval_in_minutes'])
}


EXHIBITION_HALL = {
    'start_time_in_hour': 8,
    'end_time_in_hour': 17,
    'number_of_zones': 12,
    'number_of_ahu': 12,
    'number_of_district_heating': 1,

    'return_temperature_setpoint_closed': 25,
    'return_temperature_setpoint_opened': 25,

    'ahu_on_off_closed': 0,
    'ahu_on_off_opened': 1,

    'ahu_coil_outlet_setpoint_closed': 20,
    'ahu_coil_outlet_setpoint_opened': 27.0,

    'district_heating_setpoint_closed': 30,
    'distric_heating_setpoint_opened': 60.0,

    'ahu_ventilation_on_off_closed': 0,
    'ahu_ventilation_on_off_opened': 1,

    'comfortable_temperature': 24,
    'penalty_temperature' : 23,

    'co2_upper_limit': 1000
}


CONTROLL_RANGE = {
    'setpoint_min': 22,
    "setpoint_max": 25
}

REACTIVE_CONTROL_DELTA_TEMPERATURE = {
    'coil': 0.1,
    'district_heating': -0.1,
    'return': -0.1

}
