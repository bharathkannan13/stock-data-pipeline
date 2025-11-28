# Stock Market Data Pipeline with Apache Airflow

A production-grade, containerized ETL pipeline for automated stock market data collection, validation, and storage.

## Executive Summary

This project implements an end-to-end data pipeline that demonstrates enterprise-level data engineering practices. The system fetches real-time stock market data from Alpha Vantage API, processes it through Apache Airflow orchestration, and persists it to PostgreSQL with full observability and error handling.

**Core Technologies:** Apache Airflow 2.x, Docker, PostgreSQL 13+, Python 3.9+

**Key Achievement:** Fully automated daily data ingestion with zero manual intervention required.

---

## Technical Architecture

### System Design

```
Alpha Vantage API
       ↓
Python ETL Script (fetch_and_store.py)
       ↓
Data Validation & Transformation
       ↓
PostgreSQL Database
       ↓
Apache Airflow (Orchestration & Monitoring)
```

### Infrastructure Components

- **Orchestration Layer**: Apache Airflow manages task scheduling, dependency resolution, and retry logic
- **Data Layer**: PostgreSQL provides ACID-compliant persistent storage
- **Integration Layer**: Python scripts handle API communication and data transformation
- **Container Layer**: Docker ensures environment consistency across development and production

---

## Project Structure

```
8byte-stock-data-pipeline/
│
├── dags/
│   └── stock_pipeline_dag.py          # Airflow DAG definition
│
├── scripts/
│   └── fetch_and_store.py             # ETL logic implementation
│
├── logs/                               # Airflow execution logs
├── plugins/                            # Custom Airflow plugins directory
│
├── docker-compose.yml                  # Multi-container orchestration
├── Dockerfile.app                      # Custom application container
├── requirements.txt                    # Python dependencies
├── .env                                # Environment variables (not tracked)
├── .env.example                        # Environment template
└── .gitignore                          # Git exclusions
```

---

## Feature Implementation

### Data Pipeline Capabilities

- **Automated Data Ingestion**: Scheduled daily extraction of stock market data
- **Data Quality Validation**: Built-in checks for data completeness and consistency
- **Error Handling**: Automatic retry mechanism with exponential backoff
- **Audit Logging**: Comprehensive logging of all pipeline activities
- **Scalable Design**: Easy to extend to additional stock symbols or data sources
- **Environment Isolation**: Fully containerized with no local dependency conflicts

### Pipeline Workflow

The DAG `stock_data_pipeline` executes five sequential tasks:

1. **pipeline_start** - Initializes the workflow and logs start time
2. **fetch_stock_data** - Executes the Python ETL script to retrieve stock data
3. **validate_data** - Performs data quality checks on ingested records
4. **log_completion** - Records successful completion metrics
5. **pipeline_end** - Finalizes the workflow and updates status

**Configuration:**
- Schedule: Daily at 6:00 AM UTC
- Retry Policy: 3 attempts with 5-minute delays
- Timeout: 30 minutes per task
- Catchup: Disabled (only runs for current date)

---

## Database Schema

### Table: `stock_data`

| Column      | Type              | Description                        |
|-------------|-------------------|------------------------------------|
| id          | SERIAL PRIMARY KEY| Auto-incrementing unique identifier|
| symbol      | TEXT              | Stock ticker symbol                |
| data_date   | DATE              | Trading date                       |
| open        | NUMERIC(10,2)     | Opening price                      |
| high        | NUMERIC(10,2)     | Highest price                      |
| low         | NUMERIC(10,2)     | Lowest price                       |
| close       | NUMERIC(10,2)     | Closing price                      |
| volume      | BIGINT            | Trading volume                     |
| fetched_at  | TIMESTAMP         | Data ingestion timestamp           |

**Indexes:**
- Primary key on `id`
- Composite index on `(symbol, data_date)` for efficient queries

---

## Installation & Deployment

### Prerequisites

- Docker Desktop 20.10+ and Docker Compose 2.0+
- Alpha Vantage API key (free tier available at alphavantage.co)
- Minimum 4GB RAM allocated to Docker
- Network access to Alpha Vantage API endpoints

### Step 1: Repository Setup

```bash
git clone https://github.com/YOUR_USERNAME/8byte-stock-data-pipeline
cd 8byte-stock-data-pipeline
```

### Step 2: Environment Configuration

Create `.env` file in the project root:

```bash
# Alpha Vantage API Configuration
STOCK_API_KEY=your_actual_api_key_here
STOCK_SYMBOLS=AAPL,MSFT,GOOGL,AMZN,TSLA

# PostgreSQL Configuration
POSTGRES_USER=stockuser
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=stockdb

# Database Connection for Python Scripts
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=stockdb
DB_USER=stockuser
DB_PASS=secure_password_here

# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

**Security Note:** Never commit `.env` to version control. Use `.env.example` as a template.

### Step 3: Initialize Airflow Database

```bash
docker compose up airflow-init
```

This creates necessary Airflow metadata tables and the default admin user.

### Step 4: Start All Services

```bash
docker compose up -d
```

This command starts:
- Airflow Webserver (port 8080)
- Airflow Scheduler
- PostgreSQL Database (port 5432)
- Redis (for Celery, if using CeleryExecutor)

### Step 5: Verify Deployment

Access the Airflow web interface at `http://localhost:8080`

**Default Credentials:**
- Username: `admin`
- Password: `admin`

**Important:** Change default credentials in production environments.

---

## Operational Usage

### Triggering the Pipeline Manually

1. Navigate to the Airflow UI
2. Locate the `stock_data_pipeline` DAG
3. Toggle the DAG to "On" state
4. Click "Trigger DAG" button for immediate execution

### Monitoring Pipeline Execution

- **Graph View**: Visualize task dependencies and execution status
- **Gantt Chart**: Analyze task duration and identify bottlenecks
- **Task Logs**: Access detailed logs for each task execution
- **XCom**: Inspect data passed between tasks

### Querying Stored Data

Connect to PostgreSQL using your preferred client (pgAdmin, DBeaver, psql):

```sql
-- View latest stock prices
SELECT symbol, data_date, close, volume
FROM public.stock_data
ORDER BY data_date DESC, symbol
LIMIT 20;

-- Calculate average closing price by symbol
SELECT symbol, 
       AVG(close) as avg_close,
       COUNT(*) as records
FROM public.stock_data
GROUP BY symbol;

-- Check data freshness
SELECT symbol, 
       MAX(data_date) as last_update,
       MAX(fetched_at) as last_fetch
FROM public.stock_data
GROUP BY symbol;
```

---

## Python ETL Script Details

### Script: `fetch_and_store.py`

**Core Functionality:**

1. **Environment Loading**: Reads configuration from `.env` file
2. **API Integration**: Constructs and executes HTTP requests to Alpha Vantage
3. **Data Parsing**: Extracts time series data from JSON responses
4. **Data Transformation**: Normalizes data into tabular format
5. **Database Insertion**: Uses parameterized queries to prevent SQL injection
6. **Error Management**: Implements try-catch blocks with detailed error logging

**Key Functions:**

```python
fetch_stock_data(symbol, api_key)       # API interaction
parse_time_series(response_json)        # JSON parsing
store_to_database(dataframe, conn)      # Database operations
validate_response(response)             # Data quality checks
```

**Libraries Used:**
- `requests` - HTTP client for API calls
- `psycopg2` - PostgreSQL database adapter
- `pandas` - Data manipulation and analysis
- `python-dotenv` - Environment variable management
- `logging` - Structured logging framework

---

## Configuration Management

### Airflow DAG Configuration

Key parameters in `stock_pipeline_dag.py`:

```python
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30)
}

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='Daily stock market data ingestion pipeline',
    schedule_interval='0 6 * * *',  # 6 AM UTC daily
    catchup=False,
    tags=['stock-market', 'etl', 'production']
)
```

### Docker Compose Services

The `docker-compose.yml` defines:

- **postgres**: Database service with persistent volume
- **airflow-webserver**: Web UI for monitoring
- **airflow-scheduler**: DAG execution engine
- **airflow-init**: One-time initialization service

---

## Testing & Validation

### Manual Testing Steps

1. **Verify API Connectivity:**
```bash
curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=YOUR_API_KEY"
```

2. **Check Database Connection:**
```bash
docker exec -it <postgres_container_id> psql -U stockuser -d stockdb -c "SELECT COUNT(*) FROM stock_data;"
```

3. **Validate Airflow Scheduler:**
```bash
docker logs <airflow_scheduler_container_id> | grep "stock_data_pipeline"
```

### Data Quality Checks

The pipeline includes automated validation:
- Non-null checks on critical fields
- Date range validation
- Duplicate detection based on `(symbol, data_date)`
- Volume threshold validation (flags unusual trading activity)

---

## Troubleshooting Guide

### Common Issues

**Issue: Airflow webserver not accessible**
- Solution: Check if port 8080 is already in use, verify Docker containers are running with `docker ps`

**Issue: API rate limit exceeded**
- Solution: Alpha Vantage free tier allows 5 API calls per minute. Add delay between requests or upgrade to premium tier

**Issue: Database connection errors**
- Solution: Ensure `host.docker.internal` resolves correctly. On Linux, use `172.17.0.1` or container name instead

**Issue: DAG not appearing in UI**
- Solution: Check DAG file syntax with `docker exec <airflow_webserver> python /opt/airflow/dags/stock_pipeline_dag.py`

---

## Production Considerations

### Security Hardening

- Rotate database credentials regularly
- Use Airflow's connection management instead of environment variables
- Implement API key rotation for Alpha Vantage
- Enable SSL/TLS for PostgreSQL connections
- Restrict network access using Docker networks

### Performance Optimization

- Add database indexes on frequently queried columns
- Implement connection pooling for database operations
- Use batch inserts instead of row-by-row insertion
- Cache API responses to reduce redundant calls
- Consider horizontal scaling with CeleryExecutor

### Monitoring & Alerting

- Configure Airflow email alerts for task failures
- Integrate with Prometheus for metrics collection
- Set up Grafana dashboards for visualization
- Implement custom health check endpoints
- Use Airflow SLAs to detect delayed executions

---

## Extension Opportunities

This pipeline can be extended to:

- Ingest additional data sources (cryptocurrency, forex, commodities)
- Implement real-time streaming with Kafka or Spark Streaming
- Add data quality dashboards using Superset or Metabase
- Create materialized views for analytical queries
- Integrate with ML models for price prediction
- Build REST API for data access
- Implement data versioning and time travel queries

---

## Technical Decisions & Rationale

**Why Airflow?**
- Industry-standard orchestration tool with rich UI and extensive plugin ecosystem
- Powerful DAG-based programming model for complex workflows
- Built-in retry, monitoring, and alerting capabilities

**Why PostgreSQL?**
- ACID compliance ensures data integrity
- Rich SQL feature set for complex analytical queries
- Excellent Python integration via psycopg2
- Free and open-source with strong community support

**Why Docker?**
- Eliminates "works on my machine" problems
- Simplifies deployment across environments
- Enables easy scaling and service isolation
- Widely adopted in enterprise environments

---

## Deliverables

This project demonstrates proficiency in:

- Designing and implementing production ETL pipelines
- Container orchestration and Docker best practices
- SQL database design and optimization
- Python programming for data engineering
- Workflow orchestration with Apache Airflow
- API integration and error handling
- Git version control and documentation

---

## Author

**Bharath Kannan R**  
Data | Python | Apache Airflow | PostgreSQL | Docker

*Specialized in building scalable data pipelines and ETL systems for enterprise environments*

GitHub: https://github.com/bharathkannan13 
LinkedIn:https://www.linkedin.com/in/bharath-kannan1154/

---

## License

This project is available for portfolio and educational purposes. For commercial use, please contact the author.

---

## Acknowledgments

- Alpha Vantage for providing free stock market data API
- Apache Software Foundation for Airflow
- PostgreSQL Global Development Group
- Docker Inc. for containerization platform

---

*Last Updated: November 2025*
