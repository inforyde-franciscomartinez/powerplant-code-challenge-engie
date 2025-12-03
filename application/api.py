import logging

from application.calculator import ProductionPlanCalculator
from application.main import app
from application.models import ProductionPlanRequest, ProductionPlanResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/productionplan", response_model=ProductionPlanResponse, tags=["Production Plan"])
def productionplan(request: ProductionPlanRequest) -> ProductionPlanResponse:
    """Calculate production plan for power plants."""
    logger.info(f"Calculating production plan for load={request.load} MW")

    calculator = ProductionPlanCalculator(request)
    result = calculator.calculate_production_plan()

    logger.info(f"Production plan calculated: {sum(p.p for p in result)} MW")
    return result
