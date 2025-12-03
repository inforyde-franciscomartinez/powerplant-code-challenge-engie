from application.calculator import ProductionPlanCalculator
from application.models import Fuels, PowerPlant, PowerPlantType, ProductionPlanRequest


def test_simple_wind_only():
    """Test with only wind turbines."""
    request = ProductionPlanRequest(
        load=100,
        fuels=Fuels(
            **{
                "gas(euro/MWh)": 10.0,
                "kerosine(euro/MWh)": 50.0,
                "co2(euro/ton)": 20.0,
                "wind(%)": 100,
            }
        ),
        powerplants=[
            PowerPlant(
                name="wind1",
                type=PowerPlantType.WINDTURBINE,
                efficiency=1.0,
                pmin=0,
                pmax=100,
            )
        ],
    )

    calculator = ProductionPlanCalculator(request)
    result = calculator.calculate_production_plan()

    assert len(result) == 1
    assert result[0].name == "wind1"
    assert result[0].p == 100.0


def test_merit_order_gas_vs_turbojet():
    """Test that gas-fired plants are preferred over turbojets."""
    request = ProductionPlanRequest(
        load=100,
        fuels=Fuels(
            **{
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20.0,
                "wind(%)": 0,
            }
        ),
        powerplants=[
            PowerPlant(
                name="gas1",
                type=PowerPlantType.GASFIRED,
                efficiency=0.53,
                pmin=0,
                pmax=100,
            ),
            PowerPlant(
                name="tj1",
                type=PowerPlantType.TURBOJET,
                efficiency=0.3,
                pmin=0,
                pmax=100,
            ),
        ],
    )

    calculator = ProductionPlanCalculator(request)
    result = calculator.calculate_production_plan()

    # Gas should be used, not turbojet
    gas_output = next(r for r in result if r.name == "gas1")
    tj_output = next(r for r in result if r.name == "tj1")

    assert gas_output.p == 100.0
    assert tj_output.p == 0.0


def test_wind_has_priority():
    """Test that wind turbines are always used first (cost = 0)."""
    request = ProductionPlanRequest(
        load=50,
        fuels=Fuels(
            **{
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20.0,
                "wind(%)": 50,
            }
        ),
        powerplants=[
            PowerPlant(
                name="wind1",
                type=PowerPlantType.WINDTURBINE,
                efficiency=1.0,
                pmin=0,
                pmax=100,
            ),
            PowerPlant(
                name="gas1",
                type=PowerPlantType.GASFIRED,
                efficiency=0.53,
                pmin=0,
                pmax=100,
            ),
        ],
    )

    calculator = ProductionPlanCalculator(request)
    result = calculator.calculate_production_plan()

    wind_output = next(r for r in result if r.name == "wind1")
    gas_output = next(r for r in result if r.name == "gas1")

    # Wind should provide 50 MW (50% of 100 pmax), gas provides the rest
    assert wind_output.p == 50.0
    assert gas_output.p == 0.0


def test_payload3_example():
    """Test with example payload 3 from the challenge."""
    request = ProductionPlanRequest(
        load=910,
        fuels=Fuels(
            **{
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20.0,
                "wind(%)": 60,
            }
        ),
        powerplants=[
            PowerPlant(
                name="gasfiredbig1",
                type=PowerPlantType.GASFIRED,
                efficiency=0.53,
                pmin=100,
                pmax=460,
            ),
            PowerPlant(
                name="gasfiredbig2",
                type=PowerPlantType.GASFIRED,
                efficiency=0.53,
                pmin=100,
                pmax=460,
            ),
            PowerPlant(
                name="gasfiredsomewhatsmaller",
                type=PowerPlantType.GASFIRED,
                efficiency=0.37,
                pmin=40,
                pmax=210,
            ),
            PowerPlant(
                name="tj1",
                type=PowerPlantType.TURBOJET,
                efficiency=0.3,
                pmin=0,
                pmax=16,
            ),
            PowerPlant(
                name="windpark1",
                type=PowerPlantType.WINDTURBINE,
                efficiency=1.0,
                pmin=0,
                pmax=150,
            ),
            PowerPlant(
                name="windpark2",
                type=PowerPlantType.WINDTURBINE,
                efficiency=1.0,
                pmin=0,
                pmax=36,
            ),
        ],
    )

    calculator = ProductionPlanCalculator(request)
    result = calculator.calculate_production_plan()

    # Check total equals load
    total = sum(r.p for r in result)
    assert abs(total - 910) < 0.1

    # Wind should be used at 60%
    wind1 = next(r for r in result if r.name == "windpark1")
    wind2 = next(r for r in result if r.name == "windpark2")
    assert abs(wind1.p - 90.0) < 0.1  # 60% of 150
    assert abs(wind2.p - 21.6) < 0.1  # 60% of 36
