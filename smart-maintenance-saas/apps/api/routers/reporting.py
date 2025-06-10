from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth # Updated to use api_key_auth
from data.schemas import ReportRequest, ReportResult
# Assuming ReportingAgent might be found in a path like this, adjust if necessary
# from apps.agents.reporting_agent import ReportingAgent

router = APIRouter()

@router.post("/generate", response_model=ReportResult, status_code=200, dependencies=[Security(api_key_auth, scopes=["reports:generate"])])
async def generate_report_endpoint(
    report_request: ReportRequest,
    request: Request,
):
    """
    Generates a report based on the specified parameters.

    This endpoint interfaces with the `ReportingAgent` to produce reports,
    which can include Key Performance Indicators (KPIs), textual summaries,
    and visualizations (charts).

    This endpoint is secured by an API key.

    Args:
        report_request (ReportRequest): The request object specifying the report to generate.
                                        This includes:
                                        - `report_type`: (e.g., "anomaly_summary", "maintenance_overview")
                                        - `format`: ("json", "text")
                                        - `time_range_start` (optional): Start datetime for the report period.
                                        - `time_range_end` (optional): End datetime for the report period.
                                        - `parameters` (optional): Additional key-value parameters for the report.
                                        - `include_charts` (optional): Boolean to include charts (if applicable).
        request (Request): The FastAPI request object, used to access the ReportingAgent
                           via the system coordinator.

    Returns:
        ReportResult: An object containing the generated report. This includes:
                      - `report_id`: Unique ID for the report.
                      - `report_type`: The type of report generated.
                      - `format`: The format of the report content.
                      - `content`: The main report content (JSON string or text).
                      - `generated_at`: Timestamp of report generation.
                      - `charts_encoded` (optional): Dictionary of base64 encoded charts.
                      - `metadata` (optional): Metadata about the report generation.
                      - `error_message` (optional): If report generation failed.

    Raises:
        HTTPException:
            - 500: If the system coordinator or ReportingAgent is not available.
            - 500: If there's an error during report generation.
            - 500: If a configuration error occurs (e.g., agent not found).
    """
    try:
        # Accessing the coordinator and then the reporting_agent
        # Ensure SystemCoordinator and its agents are initialized and available in app.state
        coordinator = request.app.state.coordinator
        if not coordinator:
            raise HTTPException(status_code=500, detail="System coordinator not available.")

        reporting_agent = coordinator.reporting_agent
        if not reporting_agent:
            raise HTTPException(status_code=500, detail="Reporting agent not available on coordinator.")

        # The generate_report method in ReportingAgent is synchronous
        # For now, calling it directly
        report_result: ReportResult = reporting_agent.generate_report(report_request)

        if report_result is None:
            raise HTTPException(status_code=500, detail="Report generation failed or returned no result.")

        return report_result
    except AttributeError as e:
        # This can happen if 'coordinator' or 'reporting_agent' is not found
        # Or if 'reporting_agent' does not have 'generate_report'
        # Consider logging the error e
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except HTTPException:
        # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        # Log the exception details here if logging is set up
        # Consider logging the error e
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
