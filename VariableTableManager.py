# coding=utf-8
from collections import deque

class VariableTableManager:
    def __init__(self, variable_array, time_window_max_width):
        self.table = deque([[None for col in range(len(variable_array))] for row in range(time_window_max_width)])
        self.variable_to_index_dict = dict()
        self.time_window_start_index = 0
        self.time_window_current_index = -1
        self.time_window_max_width = time_window_max_width
        self.last_variable_column_index = -1

        for variable in variable_array:
            self._register_new_variable_to_index_dict(variable["ID"])

    def _register_new_variable_to_index_dict(self, variable_name):
        if variable_name in self.variable_to_index_dict:
            raise KeyError(variable_name + ' is already registered')
        else:
            self.last_variable_column_index += 1
            self.variable_to_index_dict[variable_name] = self.last_variable_column_index

    def set_value(self, variable_name, time_index, value):
        # print self.time_window_current_index + time_index

        if variable_name in self.variable_to_index_dict:
            if self.time_window_current_index + time_index < self.time_window_start_index or \
                                    self.time_window_current_index + time_index >= self.time_window_max_width:
                raise IndexError('index ' + str(time_index) + ' is out of range')
            else:
                self.table[self.time_window_current_index + time_index][self.variable_to_index_dict[variable_name]] = value
        else:
            raise KeyError('variable ' + variable_name + ' is not registered')

    def get_value(self, variable_name, time_index):
        # print "current time index"
        # print self.time_window_current_index
        # print "time index"
        # print time_index
        if variable_name in self.variable_to_index_dict:
            if self.time_window_current_index + time_index < self.time_window_start_index or \
                                    self.time_window_current_index + time_index >= self.time_window_max_width:
                raise IndexError('index ' + str(time_index) + ' is out of range')
            else:
                return self.table[self.time_window_current_index + time_index][self.variable_to_index_dict[variable_name]]
        else:
            raise KeyError('variable ' + variable_name + ' is not registered')

    def clear(self):
        self.time_window_current_index = 0
        for row in range(self.time_window_max_width):
            for col in range(len(self.variable_to_index_dict)):
                self.table[row][col] = None

    def shift(self):
        if self.time_window_current_index >= self.time_window_max_width-1:
            self.table.rotate(-1)
            for col in range(len(self.variable_to_index_dict)):
                self.table[self.time_window_current_index][col] = None

    def update_time_window(self):
        if self.time_window_current_index + 1 < self.time_window_max_width:
            self.time_window_current_index = self.time_window_current_index + 1