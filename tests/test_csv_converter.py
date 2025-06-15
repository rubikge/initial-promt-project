import pytest
import pandas as pd
from pydantic import BaseModel, Field
from csv_converter.csv_converter import convert_csv_to_pydantic, convert_pydantic_to_csv


class CustomModel(BaseModel):
    name: str = Field(alias="Name")
    age: int = Field(alias="Age")
    city: str = Field(alias="City")


@pytest.fixture
def custom_csv_path(tmp_path):
    """Create a temporary CSV file with custom model data."""
    df = pd.DataFrame({
        "Name": ["John", "Alice"],
        "Age": [30, 25],
        "City": ["New York", "London"]
    })
    file_path = tmp_path / "test_custom.csv"
    df.to_csv(file_path, index=False)
    return file_path


def test_convert_csv_to_pydantic(custom_csv_path):
    """Test converting CSV to Pydantic models."""
    custom_objects = convert_csv_to_pydantic(custom_csv_path, CustomModel)
    
    assert len(custom_objects) == 2
    assert isinstance(custom_objects[0], CustomModel)
    assert custom_objects[0].name == "John"
    assert custom_objects[0].age == 30
    assert custom_objects[0].city == "New York"


def test_convert_pydantic_to_csv(tmp_path):
    """Test converting Pydantic models to CSV."""
    custom_objects = [
        CustomModel(Name="John", Age=30, City="New York"),
        CustomModel(Name="Alice", Age=25, City="London")
    ]
    
    output_path = tmp_path / "output.csv"
    convert_pydantic_to_csv(custom_objects, output_path)
    
    # Verify the output file exists and contains correct data
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert df["Name"].iloc[0] == "John"
    assert df["Age"].iloc[0] == 30
    assert df["City"].iloc[1] == "London"


def test_convert_csv_to_pydantic_with_invalid_data(tmp_path):
    """Test converting CSV to Pydantic models with invalid data."""
    df = pd.DataFrame({
        "Name": ["John"],
        "Age": ["invalid"],  # Invalid integer value
        "City": ["New York"]
    })
    file_path = tmp_path / "test_invalid.csv"
    df.to_csv(file_path, index=False)
    
    with pytest.raises(Exception):
        convert_csv_to_pydantic(file_path, CustomModel)


def test_convert_csv_to_pydantic_with_missing_required_fields(tmp_path):
    """Test converting CSV to Pydantic models with missing required fields."""
    df = pd.DataFrame({
        "Name": ["John"],
        "Age": [30]
        # Missing required field "City"
    })
    file_path = tmp_path / "test_missing_fields.csv"
    df.to_csv(file_path, index=False)
    
    with pytest.raises(Exception):
        convert_csv_to_pydantic(file_path, CustomModel)
