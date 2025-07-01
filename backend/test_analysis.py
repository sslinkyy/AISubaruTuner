import pandas as pd

import pytest

from .datalog_analyzer import DatalogAnalyzer
from .enhanced_ai_suggestions import generate_enhanced_ai_suggestions


@pytest.fixture
def datalog_csv_path(tmp_path) -> str:
    """Create a small sample datalog CSV for testing."""
    df = pd.DataFrame(
        {
            "A/F Sensor #1 (AFR)": [14.7, 14.8, 14.6],
            "A/F Correction #1 (%)": [1.0, -2.0, 0.5],
            "Knock Sum": [0, 1, 0],
            "Manifold Absolute Pressure (psi)": [10, 12, 15],
        }
    )
    path = tmp_path / "datalog.csv"
    df.to_csv(path, index=False)
    return str(path)

from .datalog_analyzer import DatalogAnalyzer
from .enhanced_ai_suggestions import generate_enhanced_ai_suggestions


def test_analysis(datalog_csv_path):
    # Initialize analyzer
    analyzer = DatalogAnalyzer()

    # Run datalog analysis
    analysis_result = analyzer.analyze_datalog(datalog_csv_path)
    print("Datalog Analysis Summary:")
    print(analysis_result["summary"])

    # Load datalog CSV as DataFrame
    df = pd.read_csv(datalog_csv_path)

    # Prepare datalog dict for AI suggestions
    datalog_dict = {
        "data": df.to_dict(orient="records"),
        "columns": list(df.columns),
        "total_rows": analysis_result["summary"]["total_rows"],
        "total_columns": analysis_result["summary"]["total_columns"]
    }

    # Generate AI suggestions
    ai_suggestions = generate_enhanced_ai_suggestions({
        "datalog": datalog_dict,
        "tune": {},  # Add tune info if available
        "platform": "Subaru",  # or your detected platform
        "issues": analysis_result.get("issues", [])
    })

    print("\nAI Suggestions:")
    for suggestion in ai_suggestions:
        print("Suggestion keys:", suggestion.keys())  # Debug keys
        title = suggestion.get('type') or suggestion.get('id') or "No Title"
        description = suggestion.get('description') or "No Description"
        print(f"- {title}: {description}")


if __name__ == "__main__":
    # Replace with your actual datalog CSV path if running manually
    datalog_csv_path = "sample_datalog.csv"
    test_analysis(datalog_csv_path)

