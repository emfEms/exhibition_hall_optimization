# coding=utf-8
WINTER = 0
SUMMER = 1
OTHER = 2
TIMESTEP = 5


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
        if pt.check_and_retrieve_price(minute) == -1:
            continue
        else:
            return pt.check_and_retrieve_price(minute)


def district_heat(time):
    LOW_LOAD = 0
    HIGH_LOAD = 1
    priceList = [79.38, 96.1]  # MCal당 요금임, 단위가 다를 경우 변환 바람

    priceTagList = [PriceTag(0, 420, priceList[LOW_LOAD]),
                    PriceTag(421, 600, priceList[HIGH_LOAD]),
                    PriceTag(601, 1439, priceList[LOW_LOAD])]

    sec_in_day = time % 86400
    minute = sec_in_day / 60

    for pt in priceTagList:
        if pt.check_and_retrieve_price(minute) == -1:
            continue
        else:
            return pt.check_and_retrieve_price(minute)


def natural_gas():
    return 6.2279
