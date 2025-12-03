# Power Plant Production Plan API

REST API to calculate optimal production plans using merit-order algorithm.

## Installation and Execution

```bash
# Install dependencies
poetry install

# Run the API
# Make sure you are using the env created by poetry
cd application
python main.py
```

The API will be available at `http://localhost:8888`

## Testing the API
To verify it works, test the API by sending payload3.json and it will return response3.json

You can also run `pytest` to execute and inspect the test suite.


**Interactive documentation**: `http://localhost:8888/docs`

## Algorithm

1. Calculate cost/MWh (fuel + CO2)
2. Sort plants by cost (merit-order)
3. Allocate load respecting pmin/pmax
4. Redistribute to meet exact load

## Project Structure

```
powerplant-coding-challenge/
├── application/
│   ├── __init__.py
│   ├── api.py           # FastAPI application and endpoints
│   ├── models.py        # Pydantic models with validations
│   ├── calculator.py    # Merit-order algorithm
│   └── main.py          # Entry point
├── tests/
│   ├── __init__.py
│   └── test_calculator.py
├── example_payloads/    # Example payloads
├── pyproject.toml       # Project configuration
└── README.md
```


### Run unit tests

```bash
pytest tests/ -v
```

## Considerations

- The algorithm respects pmin/pmax constraints for each plant
- Gas-fired and turbojet plants include CO2 emission costs
- Wind turbines generate according to available wind percentage
- The sum of all generated power must exactly match the required load
- Power from each plant is a multiple of 0.1 MW

## Author

Francisco Martinez Lopez - francisco.martinez@inforyde.com
