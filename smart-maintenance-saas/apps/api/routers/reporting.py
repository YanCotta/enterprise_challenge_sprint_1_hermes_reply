from fastapi import APIRouter, Request, HTTPException, Depends
from smart_maintenance_saas.apps.api.dependencies import get_api_key
from smart_maintenance_saas.data.schemas import ReportRequest, ReportResult
# Assuming ReportingAgent might be found in a path like this, adjust if necessary
# from smart_maintenance_saas.apps.agents.reporting_agent import ReportingAgent

router = APIRouter()

@router.post("/reports/generate", response_model=ReportResult, status_code=200, dependencies=[Depends(get_api_key)])
async def generate_report_endpoint(
    report_request: ReportRequest,
    request: Request,
):
    """
    Generates a report by calling the ReportingAgent.
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

        # The generate_report method in ReportingAgent needs to be an async method
        # or run in a thread pool if it's synchronous and IO-bound.
        # For now, assuming it can be awaited or is fast enough.
        report_result: ReportResult = await reporting_agent.generate_report(report_request)

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
