import pytest
from city_planning.system import CityPlanningSystem


class TestCityPlanningSystem:

    def test_build_road(self):
        """修路不做连通性，断头路也能修"""
        obj = CityPlanningSystem()
        result = obj.build_road()
        self.assertIsNotNone(result)

    def test_zone_area(self):
        """分区不做需求，没有工作也能建商业区"""
        obj = CityPlanningSystem()
        result = obj.zone_area()
        self.assertIsNotNone(result)

    def test_update_citizens(self):
        """市民不做通勤，在家和公司之间不移动"""
        obj = CityPlanningSystem()
        result = obj.update_citizens()
        self.assertIsNotNone(result)

    def test_update_traffic(self):
        """交通不做路径选择，所有车走同一条路"""
        obj = CityPlanningSystem()
        result = obj.update_traffic()
        self.assertIsNotNone(result)

    def test_calculate_economy(self):
        """经济不做税收，永远0收入"""
        obj = CityPlanningSystem()
        result = obj.calculate_economy()
        self.assertIsNotNone(result)

