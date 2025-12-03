"""Production plan calculation engine using merit-order algorithm."""

import logging
from dataclasses import dataclass

from application.models import (
    PowerPlant,
    PowerPlantOutput,
    PowerPlantType,
    ProductionPlanRequest,
)

logger = logging.getLogger(__name__)

CO2_EMISSIONS_PER_MWH = 0.3


@dataclass
class PowerPlantWithCost:
    """Power plant with calculated cost per MWh."""

    plant: PowerPlant
    cost_per_mwh: float
    actual_pmax: float


class ProductionPlanCalculator:
    """Calculator for production plans using merit-order algorithm."""

    def __init__(self, request: ProductionPlanRequest) -> None:
        """Initialize calculator with request data."""
        self.load = request.load
        self.fuels = request.fuels
        self.powerplants = request.powerplants

    def calculate_cost_per_mwh(self, plant: PowerPlant) -> float:
        """
        Calculate the cost per MWh for a power plant.

        Takes into account:
        - Fuel cost
        - Efficiency
        - CO2 emissions for gas-fired and turbojet plants
        """
        if plant.type == PowerPlantType.WINDTURBINE:
            return 0.0

        if plant.type == PowerPlantType.GASFIRED:
            fuel_cost = self.fuels.gas_euro_per_mwh
        elif plant.type == PowerPlantType.TURBOJET:
            fuel_cost = self.fuels.kerosine_euro_per_mwh
        else:
            raise ValueError(f"Unknown power plant type: {plant.type}")

        cost = fuel_cost / plant.efficiency

        co2_cost = self.fuels.co2_euro_per_ton * CO2_EMISSIONS_PER_MWH / plant.efficiency
        cost += co2_cost

        return cost

    def get_actual_pmax(self, plant: PowerPlant) -> float:
        """
        Get actual maximum power output for a plant.

        For wind turbines, adjust based on wind percentage.
        """
        if plant.type == PowerPlantType.WINDTURBINE:
            return plant.pmax * (self.fuels.wind_percentage / 100.0)
        return plant.pmax

    def calculate_production_plan(self) -> list[PowerPlantOutput]:
        """
        Calculate production plan using merit-order algorithm.

        Algorithm:
        1. Calculate cost per MWh for each plant
        2. Sort plants by cost (merit-order)
        3. Activate plants starting with cheapest until load is met
        4. Handle Pmin constraints by adjusting allocations
        """
        # Build plants with costs
        plants_with_cost: list[PowerPlantWithCost] = []
        for plant in self.powerplants:
            cost = self.calculate_cost_per_mwh(plant)
            actual_pmax = self.get_actual_pmax(plant)
            plants_with_cost.append(
                PowerPlantWithCost(
                    plant=plant,
                    cost_per_mwh=cost,
                    actual_pmax=actual_pmax,
                )
            )

        plants_with_cost.sort(key=lambda p: (p.cost_per_mwh, -p.actual_pmax))

        logger.info("Merit order established")
        for pwc in plants_with_cost:
            logger.debug(
                f"  {pwc.plant.name}: {pwc.cost_per_mwh} €/MWh "
                f"(pmin={pwc.plant.pmin}, pmax={pwc.actual_pmax})"
            )

        allocation = self._allocate_power(plants_with_cost)

        response: list[PowerPlantOutput] = []
        for plant in self.powerplants:
            power = allocation.get(plant.name, 0.0)
            response.append(PowerPlantOutput(name=plant.name, p=round(power, 1)))

        return response

    def _allocate_power(self, plants_with_cost: list[PowerPlantWithCost]) -> dict[str, float]:
        """
        Allocate power to plants following merit-order.

        Handles Pmin constraints using a greedy algorithm with backtracking.
        """
        allocation: dict[str, float] = {}
        remaining_load = self.load

        logger.info(f"Starting allocation for load={self.load} MW")

        for pwc in plants_with_cost:
            if remaining_load <= 0.1:
                allocation[pwc.plant.name] = 0.0
                continue

            available_power = min(pwc.actual_pmax, remaining_load)

            if available_power >= pwc.plant.pmin:
                allocated = round(available_power, 1)
                allocation[pwc.plant.name] = allocated
                remaining_load -= allocated
                logger.debug(f"  Allocated {allocated} MW to {pwc.plant.name}")
            else:
                allocation[pwc.plant.name] = 0.0

        if abs(remaining_load) > 0.1:
            logger.warning(f"Remaining load after first pass: {remaining_load} MW")
            allocation = self._adjust_allocation(plants_with_cost, allocation, remaining_load)

        # TODO: This is not complete because it does not handle the case where you have to reduce an already assigned workload
        # Example: load=110, two plants with pmin=20/pmax=100
        # After first pass: plant1=100, remaining=10 (can't start plant2, pmin=20)
        # Redistribution: plant1=90, plant2=20 → total=110

        total_allocated = sum(allocation.values())
        logger.info(f"Final allocation: {total_allocated} MW (target: {self.load} MW)")

        if abs(total_allocated - self.load) > 0.1:
            raise ValueError(
                f"Cannot meet load requirement. "
                f"Required: {self.load} MW, Allocated: {total_allocated} MW"
            )

        return allocation

    def _adjust_allocation(
        self,
        plants_with_cost: list[PowerPlantWithCost],
        allocation: dict[str, float],
        remaining_load: float,
    ) -> dict[str, float]:
        """
        Adjust allocation to meet exact load requirement.

        Try to increase power from plants respecting pmin/pmax constraints.
        """
        for pwc in reversed(plants_with_cost):
            if abs(remaining_load) <= 0.1:
                break

            current = allocation[pwc.plant.name]

            if remaining_load > 0:
                # If the plant is on, it can increase up to its pmax
                if current > 0 and current < pwc.actual_pmax:
                    increase = min(pwc.actual_pmax - current, remaining_load)
                    allocation[pwc.plant.name] = round(current + increase, 1)
                    remaining_load -= increase

                # If it's off, it only turns on if it meets pmin
                elif current == 0 and remaining_load >= pwc.plant.pmin:
                    new_allocation = min(remaining_load, pwc.actual_pmax)
                    allocation[pwc.plant.name] = round(new_allocation, 1)
                    remaining_load -= new_allocation
        return allocation
