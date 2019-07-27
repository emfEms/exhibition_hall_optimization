# coding=utf-8

# 에뮬레이터
process_filepath = ".\..\Process.idf" ## idf 파일 경로를 설정했는지 확인할 것

# 실제 재실인원, 외기 co2
actual_exhibition_hall_circumstance_filepath = ".\ExhibitionHallCircumstance\ActualExhibitionHallCircumstance.csv"

# 재실인원 예측 파일
predicted_occupants_filepath = ".\ExhibitionHallCircumstance\Occupants.csv"
# 외기 예보
forecast_filepath = ".\ExhibitionHallCircumstance\Forecast.csv"

# 테이블 변수 파일 경로
accumulation_table_variables_filepath = ".\Variable\Accumulation_Table_Variables.json"
simulation_table_variables_filepath = ".\Variable\Simulation_Table_Variables.json"

# 제어할 스케줄 대상 id 파일 경로
PATH_ID_ORDER_IN_SCHEDULE = ".\Variable\id_order_in_schedule.json"

# ADJACENT_ZONES 파일의 경로
PATH_ADJACENT_ZONES_TEMPERATURE = ".\Variable/adjacent_zones_temperature.json"

# inputs attribute 파일의 경로
PATH_INPUT_ATTRIBUTES_OUTDOOR_TEMPERATURE = "./Variable/input_attributes/outdoor_temperature_model.json"
PATH_INPUT_ATTRIBUTES_ENERGY = "./Variable/input_attributes/electric_energy_model.json"
PATH_INPUT_ATTRIBUTES_DISTRICT_HEATING = "./Variable/input_attributes/district_heating_energy_model.json"

PATH_INPUT_ATTRIBUTES_ZONE_TEMPERATURE = \
    ["./Variable/input_attributes/zone_01_temperature_model.json",
     "./Variable/input_attributes/zone_02_temperature_model.json",
     "./Variable/input_attributes/zone_03_temperature_model.json",
     "./Variable/input_attributes/zone_04_temperature_model.json",
     "./Variable/input_attributes/zone_05_temperature_model.json",
     "./Variable/input_attributes/zone_06_temperature_model.json",
     "./Variable/input_attributes/zone_07_temperature_model.json",
     "./Variable/input_attributes/zone_08_temperature_model.json",
     "./Variable/input_attributes/zone_09_temperature_model.json",
     "./Variable/input_attributes/zone_10_temperature_model.json",
     "./Variable/input_attributes/zone_11_temperature_model.json",
     "./Variable/input_attributes/zone_12_temperature_model.json"
     ]

# 학습 모형 파일의 경로
PATH_PREDICTION_MODEL_OUTDOOR_TEMPERATURE = "./SimulationModel/outdoor_1_1_MultilayerPerceptron.model"
PATH_PREDICTION_MODEL_ENERGY = "./SimulationModel/electric_1_1_MultilayerPerceptron.model"
PATH_PREDICTION_MODEL_DISTRICT_HEATING = "./SimulationModel/cooling_1_1_MultilayerPerceptron.model"
PATH_PREDICTION_MODEL_ZONE_TEMPERATURE = ["./SimulationModel/zone1_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone2_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone3_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone4_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone5_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone6_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone7_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone8_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone9_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone10_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone11_1_1_MultilayerPerceptron.model",
                                          "./SimulationModel/zone12_1_1_MultilayerPerceptron.model"]
