import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import user_routes, project_routes, report_routes, task_routes, group_routes, evaluation_routes, github_routes, upload, free_rider
from database import init_db
from config import env
import logging
# OpenTelemetry
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# from opentelemetry import trace
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry import metrics
# from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

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
# resource = Resource.create(attributes={
#     SERVICE_NAME: "itss-be-service"
# })
# tracerProvider = TracerProvider(resource=resource)
# processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
# tracerProvider.add_span_processor(processor)
# trace.set_tracer_provider(tracerProvider)

# reader = PeriodicExportingMetricReader(
#     OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics")
# )
# meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
# metrics.set_meter_provider(meterProvider)

app_instance = FastAPIApp().app
# FastAPIInstrumentor.instrument_app(app_instance)

if __name__ == "__main__":  
    uvicorn.run("main:app_instance", host=env.HOST, port=env.PORT, reload=True)