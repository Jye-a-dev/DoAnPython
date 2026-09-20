from flask_restx import Namespace, Resource, fields
from sqlalchemy import text

from server.core.config import PIPELINE_SERVICE_URL
from server.database import get_db_session

ns_health = Namespace("Health Check", path="/", description="Service telemetry and DB state")

health_model = ns_health.model("HealthCheckResponse", {
    "status": fields.String,
    "service": fields.String,
    "sqlite_connected": fields.Boolean,
    "pipeline_target": fields.String
})


@ns_health.route("/health")
class HealthCheck(Resource):
    @ns_health.doc("health_check", description="Health check for Flask Gateway and SQLite database connection")
    @ns_health.response(200, "Healthy", health_model)
    def get(self):
        sqlite_ok = False
        try:
            with get_db_session() as session:
                session.exec(text("SELECT 1")).first()
                sqlite_ok = True
        except Exception:
            sqlite_ok = False

        return {
            "status": "healthy" if sqlite_ok else "degraded",
            "service": "flask_gateway",
            "sqlite_connected": sqlite_ok,
            "pipeline_target": PIPELINE_SERVICE_URL
        }, (200 if sqlite_ok else 500)

