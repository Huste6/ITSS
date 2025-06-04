import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import user_routes, project_routes, report_routes, task_routes, group_routes, evaluation_routes, github_routes, upload, free_rider
from database import init_db
from config import env
import logging
# OpenTelemetry
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    await init_db()
    yield 
    print("Shutting down gracefully...")

class FastAPIApp:
    def __init__(self):
        self.app = FastAPI(lifespan=lifespan)
        self.configure_cors()
        self.include_routers()

    def configure_cors(self):
        origins = ["http://localhost:4200"]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def include_routers(self):
        self.app.include_router(user_routes.router)
        self.app.include_router(project_routes.router)
        self.app.include_router(report_routes.router)   
        self.app.include_router(task_routes.router)
        self.app.include_router(group_routes.router)
        self.app.include_router(evaluation_routes.router)
        self.app.include_router(github_routes.router)
        self.app.include_router(upload.router)
        self.app.include_router(free_rider.router)

# OpenTelemetry setup
resource = Resource.create({SERVICE_NAME: "itss-service"})

# Tracing setup
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()
trace_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

# Metrics setup
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics")
)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

# App must be initialized AFTER setting providers
app_instance = FastAPIApp().app

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app_instance)

if __name__ == "__main__":  
    uvicorn.run("main:app_instance", host=env.HOST, port=env.PORT, reload=True)