from fastapi import APIRouter, Request, HTTPException, Depends, Security
from apps.api.dependencies import api_key_auth
from data.schemas import ReportRequest, ReportResult
from datetime import datetime, timezone
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
router = APIRouter()

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=4)

def _generate_report_sync(reporting_agent, report_request: ReportRequest) -> ReportResult:
    """Synchronous wrapper for report generation to run in thread pool."""
    return reporting_agent.generate_report(report_request)

@router.post("/generate", response_model=ReportResult, status_code=200, dependencies=[Security(api_key_auth, scopes=["reports:generate"])])
async def generate_report_endpoint(
    report_request: ReportRequest,
    request: Request,
):
    """
    Generates a report based on the specified parameters.
    
    This endpoint interfaces with the ReportingAgent to produce reports.
    """
    try:
        logger.info(f"Generating report: {report_request.report_type}")
        
        # Access the coordinator and reporting agent
        coordinator = request.app.state.coordinator
        if not coordinator:
            raise HTTPException(status_code=500, detail="System coordinator not available.")

        reporting_agent = coordinator.reporting_agent
        if not reporting_agent:
            raise HTTPException(status_code=500, detail="Reporting agent not available on coordinator.")

        # Call the generate_report method in a thread pool to avoid blocking
        # This prevents matplotlib and other blocking operations from causing async issues
        try:
            logger.info("Calling reporting_agent.generate_report in thread pool...")
            loop = asyncio.get_event_loop()
            report_result = await loop.run_in_executor(
                executor, 
                _generate_report_sync, 
                reporting_agent, 
                report_request
            )
            logger.info("Report generation completed successfully")
        except Exception as e:
            logger.error(f"Error in reporting_agent.generate_report: {str(e)}", exc_info=True)
            # Return a more detailed error for debugging
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

        if report_result is None:
            raise HTTPException(status_code=500, detail="Report generation returned no result.")

        return report_result
        
    except HTTPException:
        # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_report_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
