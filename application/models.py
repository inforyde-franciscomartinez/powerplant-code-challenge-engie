from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class PowerPlantType(str, Enum):
    """Types of power plants."""

    GASFIRED = "gasfired"
    TURBOJET = "turbojet"
    WINDTURBINE = "windturbine"


class Fuels(BaseModel):
    """Fuel costs and wind percentage."""

    gas_euro_per_mwh: Annotated[float, Field(alias="gas(euro/MWh)")]
    kerosine_euro_per_mwh: Annotated[float, Field(alias="kerosine(euro/MWh)")]
    co2_euro_per_ton: Annotated[float, Field(alias="co2(euro/ton)")]
    wind_percentage: Annotated[float, Field(ge=0, le=100, alias="wind(%)")]

    model_config = {"populate_by_name": True}


class PowerPlant(BaseModel):
    """Power plant specification."""

    name: str
    type: PowerPlantType
    efficiency: Annotated[float, Field(gt=0, le=1)]
    pmin: Annotated[float, Field(ge=0)]
    pmax: Annotated[float, Field(gt=0)]

    @field_validator("pmax")
    @classmethod
    def validate_pmax_greater_than_pmin(cls, pmax: float, info) -> float:
        """Validate that pmax is greater than or equal to pmin."""
        if "pmin" in info.data and pmax < info.data["pmin"]:
            raise ValueError("pmax must be greater than or equal to pmin")
        return pmax


class ProductionPlanRequest(BaseModel):
    """Request payload for production plan calculation."""

    load: Annotated[float, Field(gt=0)]
    fuels: Fuels
    powerplants: list[PowerPlant]

    @field_validator("powerplants")
    @classmethod
    def validate_powerplants_not_empty(cls, powerplants: list[PowerPlant]) -> list[PowerPlant]:
        """Validate that there is at least one power plant."""
        if not powerplants:
            raise ValueError("At least one power plant is required")
        return powerplants


class PowerPlantOutput(BaseModel):
    """Output specification for a single power plant."""

    name: str
    p: Annotated[float, Field(ge=0)]

    @field_validator("p")
    @classmethod
    def validate_power_multiple_of_point_one(cls, p: float) -> float:
        """Validate that power is a multiple of 0.1 MW."""
        rounded = round(p, 1)
        return rounded


ProductionPlanResponse = list[PowerPlantOutput]
