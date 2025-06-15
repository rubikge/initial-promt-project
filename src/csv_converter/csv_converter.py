from pathlib import Path
from pydantic import BaseModel, Field
import pandas as pd
from logger import logger
from typing import TypeVar, Type

T = TypeVar('T', bound=BaseModel)

def convert_csv_to_pydantic(file_path: str | Path, model: Type[T]) -> list[T]:
    """
    Convert CSV file to list of Pydantic models.
    
    Args:
        file_path: Path to the CSV file
        model: Pydantic model class to use for validation (defaults to Sample)
        
    Returns:
        List of Pydantic models
    """
    logger.info(f"Starting CSV to Pydantic conversion for file: {file_path}")
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()  # Strip whitespace from column names
        samples = [model(**row) for row in df.to_dict(orient="records")]
        logger.info(f"Successfully converted {len(samples)} samples from CSV")
        return samples
    except Exception as e:
        logger.error(f"Error converting CSV to Pydantic: {str(e)}")
        raise


def convert_pydantic_to_csv(samples: list[T], output_path: str | Path) -> None:
    """
    Convert list of Pydantic models to CSV file.
    
    Args:
        samples: List of Pydantic models
        output_path: Path where to save the CSV file
    """
    logger.info(f"Starting Pydantic to CSV conversion, saving to: {output_path}")
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame([sample.model_dump(by_alias=True) for sample in samples])
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved {len(samples)} samples to CSV")
    except Exception as e:
        logger.error(f"Error converting Pydantic to CSV: {str(e)}")
        raise

# Example usage
if __name__ == '__main__':
    class Sample(BaseModel):
        sample_id: str = Field(alias="Sample ID")
        tier_1_era_label: str = Field(alias="Tier 1 Era Label")
        tier_2_region_route: str = Field(alias="Tier 2 Region/Route")
        sex: str = Field(alias="Sex")
        date: str = Field(alias="Full Date One of two formats. (Format 1) 95.4% CI calibrated radiocarbon age (Conventional Radiocarbon Age BP, Lab number) e.g. 2624-2350 calBCE (3990±40 BP, Ua-35016). (Format 2) Archaeological context range, e.g. 2500-1700 BCE")
        locality: str = Field(alias="Locality")
        political_entity: str = Field(alias="Political Entity")
        latitude: float = Field(alias="Lat.")
        longitude: float = Field(alias="Long.")
        publication: str = Field(alias="Publication")
        marketing_name: str = Field(default="", alias="Marketing Name")
        description: str = Field(default="", alias="Description")

    samples = convert_csv_to_pydantic("data/samples.csv", Sample)
    convert_pydantic_to_csv(samples, "data/samples_converted.csv")