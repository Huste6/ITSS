import { ReactNode, useEffect } from 'react';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto';
import { MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-proto';
import { ATTR_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import { trace } from '@opentelemetry/api';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';

interface TraceProviderProps {
  children: ReactNode;
}

const setupOpenTelemetry = () => {
  const otelTraceEndpoint = 'http://localhost:4318/v1/traces';
  const otelMetricEndpoint = 'http://localhost:4318/v1/metrics';
  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: 'itss-fe-service',
  })

  // Tracer
  const traceExporter = new OTLPTraceExporter({
    url: otelTraceEndpoint,
  });

  const tracerProvider = new WebTracerProvider({
    resource: resource,
    spanProcessors: [new SimpleSpanProcessor(traceExporter)],
  });

  const fetchInstrumentation = new FetchInstrumentation({});
  fetchInstrumentation.setTracerProvider(tracerProvider);

  tracerProvider.register();
  trace.setGlobalTracerProvider(tracerProvider);

  // Metric
  const metricExporter = new OTLPMetricExporter({ url: otelMetricEndpoint });
  const metricReader = new PeriodicExportingMetricReader({
    exporter: metricExporter,
    exportIntervalMillis: 1000, // thu thập metrics mỗi 1 giây
  });
  
  const meterProvider = new MeterProvider({
    resource: resource,
    readers: [metricReader],
  });  

  registerInstrumentations({
    instrumentations: [getWebAutoInstrumentations(), fetchInstrumentation],
    tracerProvider,
    meterProvider,
  });

  console.log('[OTEL] OpenTelemetry initialized');
};

export default function TraceProvider({ children }: TraceProviderProps) {
  useEffect(() => {
    setupOpenTelemetry();
  }, []);

  return <>{children}</>;
}
