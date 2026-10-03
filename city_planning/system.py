"""
pairwise-city-planning-system - CityPlanningSystem

This module contains a deliberately broken implementation.
Fix all bugs so that tests pass.
"""


class CityPlanningSystem:
    def __init__(self):
        self.state = {}

    def build_road(self, *args, **kwargs):
        """BUG: 修路不做连通性，断头路也能修"""
        return None

    def zone_area(self, *args, **kwargs):
        """BUG: 分区不做需求，没有工作也能建商业区"""
        return None

    def update_citizens(self, *args, **kwargs):
        """BUG: 市民不做通勤，在家和公司之间不移动"""
        return None

    def update_traffic(self, *args, **kwargs):
        """BUG: 交通不做路径选择，所有车走同一条路"""
        return None

    def calculate_economy(self, *args, **kwargs):
        """BUG: 经济不做税收，永远0收入"""
        return None

