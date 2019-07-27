from Config import *

class PriceTag:
    def __init__(self, startTime, endTime, price):
        self.startTime = startTime
        self.endTime = endTime
        self.price = price
        pass

    def check_and_retrieve_price(self, time):
        if self.startTime <= time <= self.endTime:
            return self.price
        else:
            return -1

    startTime = 0.0
    endTime = 0.0
    price = 0.0


def electricity(time):
    LOW_LOAD = 0
    MID_LOAD = 1
    HIGH_LOAD = 2
    priceList = [56.1, 109.0, 191.1]


    priceTagList = [PriceTag(0, 540, priceList[LOW_LOAD]),
                    PriceTag(541, 600, priceList[MID_LOAD]),
                    PriceTag(601, 720, priceList[HIGH_LOAD]),
                    PriceTag(721, 780, priceList[MID_LOAD]),
                    PriceTag(781, 1020, priceList[HIGH_LOAD]),
                    PriceTag(1021, 1380, priceList[MID_LOAD]),
                    PriceTag(1381, 1439, priceList[LOW_LOAD])]

    sec_in_day = time % 86400
    minute = sec_in_day / 60

    for pt in priceTagList:
        cost = 0
        if pt.check_and_retrieve_price(minute) == -1:
            continue
        else:
            cost = pt.check_and_retrieve_price(minute)
    del priceList[:]
    del priceTagList[:]
    return cost

def natural_gas():
    return 6.2279 * SIMULATION_TIME_VARIABLE['control_interval_in_minutes']





